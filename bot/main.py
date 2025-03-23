import asyncio
import logging
import os
import tempfile
import nest_asyncio
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import threading
from bot.utilities.http_server import run_http_server
import telegram
import time  # Tambahkan import ini di bagian atas

# Muat variabel lingkungan dari .env
load_dotenv()

# Konfigurasi bot
API_TOKEN = os.getenv('API_TOKEN')
TARGET = os.getenv('TARGET').split(',')  # Ambil dari .env dan pisahkan menjadi daftar
ADMIN = os.getenv('ADMIN').split(',')    # Ambil dari .env dan pisahkan menjadi daftar

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Terapkan nest_asyncio
nest_asyncio.apply()

# Variabel status untuk mode operasi dan mode penerusan
mode_auto = False  # Default ke mode auto
mode_remof = False # Default ke mode penanda

# Variabel global untuk menyimpan waktu saat bot dimulai
start_time = time.time()

# Fungsi untuk memeriksa otorisasi
def is_authorized(user):
    return user.username in ADMIN or str(user.id) in ADMIN

# Fungsi untuk memulai bot dengan pesan sambutan
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("REPO", url="https://github.com/AlekBaikHati/forward-bot-telegram")],
        [InlineKeyboardButton("FATHER", url="https://t.me/Zerozerozoro")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        'Selamat datang di FORWARD BOT TELEGRAM! Gunakan /settings untuk mengatur mode.',
        reply_markup=reply_markup
    )

# Fungsi untuk mengatur mode bot
async def settings(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update.effective_user):
        await update.message.reply_text('Anda tidak diizinkan untuk menggunakan bot ini.')
        return

    # Kirim pesan baru untuk memilih mode
    await update.message.reply_text('Gunakan tombol di bawah untuk mengatur mode.', reply_markup=await create_mode_keyboard())

# Fungsi untuk mendapatkan teks mode aktif
async def get_active_mode_text() -> str:
    active_mode = []
    if mode_auto:
        active_mode.append("✅ AUTO")
    else:
        active_mode.append("✅ MANUAL")

    if mode_remof:
        active_mode.append("✅ REMOVE TAG")
    else:
        active_mode.append("✅ WITH TAG")

    return "Active Mode:\n" + "\n".join(active_mode)

# Fungsi untuk membuat keyboard mode
async def create_mode_keyboard() -> InlineKeyboardMarkup:
    # Tentukan emoji penanda
    auto_emoji = "📌" if mode_auto else ""
    manual_emoji = "📌" if not mode_auto else ""
    penanda_emoji = "📌" if not mode_remof else ""
    remov_emoji = "📌" if mode_remof else ""

    # Buat tombol inline
    keyboard = [
        [InlineKeyboardButton(f"{auto_emoji} AUTO", callback_data='set_auto'),
         InlineKeyboardButton(f"{manual_emoji} MANUAL", callback_data='set_manual')],
        [InlineKeyboardButton(f"{penanda_emoji} WITH TAG", callback_data='set_penanda'),
         InlineKeyboardButton(f"{remov_emoji} REMOVE TAG", callback_data='set_remov')],
        [InlineKeyboardButton("TUTUP", callback_data='close')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Fungsi untuk menangani pesan
async def forward_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update.effective_user):
        await update.message.reply_text('Anda tidak diizinkan untuk menggunakan bot ini.')
        return

    message = update.message or update.channel_post
    if not message:
        return

    if mode_auto:
        await forward_post_auto(update, context)
    else:
        await forward_post_manual(update, context)

# Fungsi untuk menangani pesan dalam mode auto
async def forward_post_auto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message or update.channel_post
    if not message:
        return

    action = "pengcopyan" if mode_remof else "penerusan"
    status_message = await message.reply_text(
        f'Memulai {action} pesan...',
        reply_to_message_id=message.message_id
    )
    error_channels = []
    success_channels = []
    total_channels = len(TARGET)

    for index, target in enumerate(TARGET):
        try:
            if mode_remof:
                await context.bot.copy_message(chat_id=target, from_chat_id=message.chat_id, message_id=message.message_id)
            else:
                await context.bot.forward_message(chat_id=target, from_chat_id=message.chat_id, message_id=message.message_id)
            success_channels.append(target)
        except Exception as e:
            logger.error(f'Gagal meneruskan pesan ke {target}: {e}')
            error_channels.append(target)

    summary_message = "Penerusan pesan selesai.\n"
    if success_channels:
        summary_message += f"Berhasil meneruskan ke: {', '.join(success_channels)}\n"
    if error_channels:
        summary_message += f"Gagal meneruskan ke: {', '.join(error_channels)}"

    await status_message.edit_text(summary_message)

# Fungsi untuk menangani pesan dalam mode manual
async def forward_post_manual(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    message = update.message or update.channel_post
    if not message:
        return

    # Mode manual, tampilkan tombol konfirmasi
    keyboard = [
        [InlineKeyboardButton("Ya", callback_data=f'confirm_forward:{message.message_id}'),
         InlineKeyboardButton("Tidak", callback_data='cancel_forward')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text('Apakah Anda ingin meneruskan pesan ini?', reply_markup=reply_markup)

# Fungsi untuk menangani tombol konfirmasi
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global mode_auto, mode_remof
    query = update.callback_query
    data = query.data

    # Menjawab callback query dengan alert jika mode sudah aktif
    if data == 'set_auto':
        if mode_auto:
            await query.answer(text="Mode AUTO sudah aktif.✨", show_alert=True)
        else:
            mode_auto = True
            mode_remof = False  # Pastikan mode REMOV dinonaktifkan saat beralih ke AUTO
            await query.answer(text="Mode diubah ke AUTO.✨", show_alert=True)
            new_text = 's\n\n' + await get_active_mode_text()
            if query.message:
                try:
                    if query.message.caption:
                        await query.message.edit_caption(new_text, reply_markup=await create_mode_keyboard())
                    else:
                        await query.message.edit_text(new_text, reply_markup=await create_mode_keyboard())
                except telegram.error.BadRequest as e:
                    logger.error(f"Failed to edit message: {e}")
    elif data == 'set_manual':
        if not mode_auto:
            await query.answer(text="Mode MANUAL sudah aktif.✨", show_alert=True)
        else:
            mode_auto = False  # Ubah ke mode manual
            await query.answer(text="Mode diubah ke MANUAL.✨", show_alert=True)
            new_text = 'Gunakan tombol di bawah untuk mengatur mode.\n\n' + await get_active_mode_text()
            if query.message:
                try:
                    if query.message.caption:
                        await query.message.edit_caption(new_text, reply_markup=await create_mode_keyboard())
                    else:
                        await query.message.edit_text(new_text, reply_markup=await create_mode_keyboard())
                except telegram.error.BadRequest as e:
                    logger.error(f"Failed to edit message: {e}")
    elif data == 'set_penanda':
        if not mode_remof:
            await query.answer(text="Mode WITH TAG sudah aktif.✨", show_alert=True)
        else:
            mode_remof = False  # Ubah ke mode penanda
            await query.answer(text="Mode diubah ke WITH TAG.✨", show_alert=True)
            new_text = 'Gunakan tombol di bawah untuk mengatur mode.\n\n' + await get_active_mode_text()
            if query.message:
                try:
                    if query.message.caption:
                        await query.message.edit_caption(new_text, reply_markup=await create_mode_keyboard())
                    else:
                        await query.message.edit_text(new_text, reply_markup=await create_mode_keyboard())
                except telegram.error.BadRequest as e:
                    logger.error(f"Failed to edit message: {e}")
    elif data == 'set_remov':
        if mode_remof:
            await query.answer(text="Mode REMOVE TAG sudah aktif.✨", show_alert=True)
        else:
            mode_remof = True  # Ubah ke mode REMOV
            await query.answer(text="Mode diubah ke REMOVE TAG.✨", show_alert=True)
            new_text = 'Gunakan tombol di bawah untuk mengatur mode.\n\n' + await get_active_mode_text()
            if query.message:
                try:
                    if query.message.caption:
                        await query.message.edit_caption(new_text, reply_markup=await create_mode_keyboard())
                    else:
                        await query.message.edit_text(new_text, reply_markup=await create_mode_keyboard())
                except telegram.error.BadRequest as e:
                    logger.error(f"Failed to edit message: {e}")
    elif data == 'close':
        await query.message.delete()
        return
    elif data.startswith('confirm_forward:'):
        # Panggil fungsi untuk meneruskan pesan
        await confirm_forward(update, context)
    elif data == 'cancel_forward':
        # Hapus pesan konfirmasi
        await cancel_forward(update, context)

# Fungsi untuk menangani konfirmasi meneruskan pesan
async def confirm_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    data = query.data.split(':')
    message_id = int(data[1])

    action = "pengcopyan" if mode_remof else "penerusan"
    status_message = await query.message.reply_text(
        f'Memulai {action} pesan...',
        reply_to_message_id=query.message.message_id
    )
    error_channels = []
    success_channels = []
    total_channels = len(TARGET)

    for index, target in enumerate(TARGET):
        try:
            if mode_remof:
                await context.bot.copy_message(chat_id=target, from_chat_id=query.message.chat_id, message_id=message_id)
            else:
                await context.bot.forward_message(chat_id=target, from_chat_id=query.message.chat_id, message_id=message_id)
            success_channels.append(target)
        except Exception as e:
            logger.error(f'Gagal meneruskan pesan ke {target}: {e}')
            error_channels.append(target)

    summary_message = "Penerusan pesan selesai.\n"
    if success_channels:
        summary_message += f"Berhasil meneruskan ke: {', '.join(success_channels)}\n"
    if error_channels:
        summary_message += f"Gagal meneruskan ke: {', '.join(error_channels)}"

    # Pastikan status_message tidak None sebelum mengedit
    if status_message:
        await status_message.edit_text(summary_message)
    await query.message.delete()

# Fungsi untuk menangani pembatalan
async def cancel_forward(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.message.delete()

# Fungsi untuk menampilkan informasi channel
async def list_channels(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update.effective_user):
        await update.message.reply_text('Anda tidak diizinkan untuk menggunakan bot ini.')
        return

    bot = context.bot
    status_message = await update.message.reply_text('Memuat daftar channel...')
    total_channels = len(TARGET)
    default_photo_url = "https://ibb.co.com/5gWGBtv1"  # URL gambar default

    # Pastikan folder 'Profil' ada
    os.makedirs('Profil', exist_ok=True)

    # Tampilkan loading sederhana untuk 0%
    await status_message.edit_text(f"Memuat daftar: 0%")

    for index, channel_id in enumerate(TARGET):
        try:
            chat = await bot.get_chat(chat_id=channel_id)
            link = f"https://t.me/{chat.username}" if chat.username else "Link tidak tersedia"
            info = (
                "✦•┈๑⋅⋯ ⋯⋅๑┈•✦\n"
                f"Channel ID: {chat.id}\n"
                f"Nama Channel: {chat.title}\n"
                f"Username Channel: {chat.username}\n"
                f"Jumlah Anggota: {await chat.get_member_count()}\n"
                f"Link Channel: {link}\n"
                "✦•┈๑⋅⋯ ⋯⋅๑┈•✦\n"
            )

            # Cek apakah channel memiliki foto profil
            if chat.photo:
                file = await bot.get_file(chat.photo.big_file_id)
                file_path = os.path.join('Profil', f"{channel_id}.jpg")
                await file.download_to_drive(custom_path=file_path)
                await bot.send_photo(chat_id=update.effective_chat.id, photo=open(file_path, 'rb'), caption=info)
                os.remove(file_path)  # Hapus file setelah dikirim
            else:
                await bot.send_photo(chat_id=update.effective_chat.id, photo=default_photo_url, caption=info)
        except Exception as e:
            await update.message.reply_text(f"Gagal mengakses channel {channel_id}: {e}")

        # Update progress setiap 10%
        progress = int((index + 1) / total_channels * 100)
        progress_bar = '█' * (progress // 10) + '▒' * (10 - (progress // 10))  # Membuat bar progres
        await status_message.edit_text(f"Memuat daftar: {progress_bar} {progress}%")

    await status_message.delete()  # Hapus pesan loading setelah selesai
    await update.message.reply_text(f'Daftar channel berhasil dimuat. Total channel: {total_channels}.', quote=True)  # Tambahkan pesan sukses dengan format quote

# Fungsi untuk menampilkan informasi channel tanpa foto
async def list_channels_no_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_authorized(update.effective_user):
        await update.message.reply_text('Anda tidak diizinkan untuk menggunakan bot ini.')
        return

    bot = context.bot
    status_message = await update.message.reply_text('Memuat daftar channel tanpa foto...')
    total_channels = len(TARGET)

    # Tampilkan loading sederhana untuk 0%
    await status_message.edit_text(f"Memuat daftar tanpa foto: 0%")

    for index, channel_id in enumerate(TARGET):
        try:
            chat = await bot.get_chat(chat_id=channel_id)
            link = f"https://t.me/{chat.username}" if chat.username else "Link tidak tersedia"
            info = (
                "⋆˖⁺‧₊☽◯☾₊‧⁺˖⋆\n"
                f"Channel ID: {chat.id}\n"
                f"Nama Channel: {chat.title}\n"
                f"Username Channel: {chat.username}\n"
                f"Jumlah Anggota: {await chat.get_member_count()}\n"
                f"Link Channel: {link}\n"
                "✦•┈๑⋅⋯ ⋯⋅๑┈•✦\n"
            )
            await update.message.reply_text(info)
        except Exception as e:
            await update.message.reply_text(f"Gagal mengakses channel {channel_id}: {e}")

        # Update progress setiap 10%
        progress = int((index + 1) / total_channels * 100)
        progress_bar = '█' * (progress // 10) + '▒' * (10 - (progress // 10))  # Membuat bar progres
        await status_message.edit_text(f"Memuat daftar tanpa foto: {progress_bar} {progress}%")

    await status_message.delete()  # Hapus pesan loading setelah selesai
    await update.message.reply_text(f'Daftar channel tanpa foto berhasil dimuat. Total channel: {total_channels}.', quote=True)  # Tambahkan pesan sukses

# Fungsi untuk menjalankan server HTTP di thread terpisah
def start_http_server():
    server_thread = threading.Thread(target=run_http_server)
    server_thread.daemon = True
    server_thread.start()

# Fungsi untuk menghitung uptime dan waktu sejak bot dimulai, serta mengukur waktu ping
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Hapus pengecekan otorisasi agar semua pengguna bisa menggunakan command ini
    # if not is_authorized(update.effective_user):
    #     await update.message.reply_text('Anda tidak diizinkan untuk menggunakan bot ini.')
    #     return

    # Hitung uptime
    current_time = time.time()
    uptime_seconds = int(current_time - start_time)
    uptime_str = time.strftime("%H:%M:%S", time.gmtime(uptime_seconds))

    # Hitung waktu ping
    start_time_ping = time.time()
    ping_message = await update.message.reply_text("Pong... 🏓")
    ping_time = (time.time() - start_time_ping) * 1000  # Hitung waktu ping dalam milidetik

    # Edit pesan untuk menampilkan hasil uptime dan ping
    await ping_message.edit_text(
        f"Ping: {ping_time:.2f} ms\n"
        f"Bot Uptime: {uptime_str}\n"
        f"Time Since Start: {uptime_seconds} detik\n"
    )

async def main() -> None:
    # Mulai server HTTP
    start_http_server()

    application = Application.builder().token(API_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settings", settings))
    application.add_handler(CommandHandler("list", list_channels))
    application.add_handler(CommandHandler("list2", list_channels_no_photo))
    application.add_handler(CommandHandler("stats", stats))  # Handler untuk /stats
    application.add_handler(MessageHandler(filters.ALL, forward_post))
    application.add_handler(CallbackQueryHandler(button))
    logger.info("Bot dimulai dan siap menerima pesan.")
    await application.run_polling()
    logger.info("Bot dihentikan.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot dihentikan oleh pengguna.")
