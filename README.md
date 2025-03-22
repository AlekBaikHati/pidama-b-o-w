
Pastikan untuk mengganti nilai di atas dengan informasi yang sesuai untuk bot Anda.

### Cara Menjalankan Bot

1. **Instal Dependensi**

   Pastikan Anda memiliki `python-dotenv` dan `python-telegram-bot` terinstal. Anda dapat menginstalnya dengan perintah berikut:

   ```
   pip install -r requirements.txt
   ```

2. **Konfigurasi Lingkungan**

   Buat file `.env` seperti yang dijelaskan di atas.

3. **Menjalankan Bot**

   Jalankan bot dengan perintah berikut:

   ```
   python -m bot.main
   ```

   Pastikan semua variabel lingkungan sudah diatur dengan benar sebelum menjalankan bot.

## Deployments

### Koyeb Deployment

[![Deploy to Koyeb](https://www.koyeb.com/static/images/deploy/button.svg)](https://app.koyeb.com/deploy?type=git&repository=github.com/AlekBaikHati/pidama-b-o-w&branch=main&name=teleshare&env%5BAPI_TOKEN%5D=your_api_token&env%5BAPI_ID%5D=your_api_id&env%5BAPI_HASH%5D=your_api_hash&env%5BTARGET%5D=-1002412629469,-1002292422802&env%5BADMIN%5D=wiburich,Ghsd77,blalil_girl)

Just set up the environment variables and you're done.

### Local Deployment

1. Clone the repo
   ```
   git clone https://github.com/zawsq/Teleshare.git
   ```
   then change directory to Teleshare 
   ```
   cd Teleshare
   ```

2. Create an .env file as described above.

3. Install requirements
   ```
   pip install -r requirements.txt
   ```

4. Start the bot.
   ```
   python -m bot.main
   ```

Dengan pembaruan ini, tombol Koyeb sekarang sudah sesuai dan siap digunakan untuk deployment. Pastikan untuk mengganti placeholder seperti `your_api_token`, `your_api_id`, dan `your_api_hash` dengan nilai yang sesuai sebelum menggunakan tombol tersebut. Jika ada bagian lain yang perlu diperbarui, silakan beri tahu saya.
