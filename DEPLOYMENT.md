# ISFT PRO — internetga chiqarishdan oldingi tekshiruv

**Holat:** sinovdan o'tgan funksional prototip; rasmiy universitet nomidan ommaviy qabulni boshlash uchun hali yakuniy audit talab etiladi. Ishlab chiqarish uchun bevosita Python `http.server` ni internetga ochish tavsiya qilinmaydi.

## Hozirgi imkoniyatlar
- Administratorga kirish, SQLite-da saqlanuvchi sessiya, CSRF, login urinishlari cheklovi.
- 16 yo'nalish, ariza qabul qilish va holatini yangilash, statistika.
- E'lon/yangilik/sahifa matnlarini boshqarish, sayt sarlavhalari va aloqa ma'lumotlarini tahrirlash.
- Sayt menyusini tahrirlash; rasmlar kutubxonasiga PNG/JPEG/WEBP/GIF yuklash.
- Har bir tugma tegishli sahifaga olib o'tishi kerak; tashqi resurslarga emas, ichki sahifalarga havolalar cheklangan.

## Lokal ishga tushirish
PowerShell:
```powershell
$env:ADMIN_PASSWORD="UzoqVaTasodifiyMaxfiyParol!2026"
python server.py
```
Birinchi ishga tushirishda admin paroli yoziladi. Keyingi safar parolni ENV orqali o'zgartirish bazadagi parolni o'zgartirmaydi.

## Server uchun
- VPS/Linux, domen va HTTPS sertifikati kerak. Reverse proxy (Nginx/Caddy) orqali HTTPS va rate limiting o'rnating.
- `ISFT_HTTPS=1` cookie `Secure` atributini yoqadi; faqat HTTPS orqali ishlating.
- `ISFT_HOST=127.0.0.1` va `PORT=8000` ni lokal portga ulang; Python standart HTTP serveri yuqori trafik uchun production-grade emas, keyinchalik Gunicorn/ASGI asosidagi servisga migratsiya tavsiya etiladi.
- `isft.db`, `isft.db-wal`, `isft.db-shm`, `uploads/` kataloglarini ommaga ochmang. Bazani SQLite backup API orqali muntazam zaxiralang va qayta tiklashni sinang.
- Haqiqiy shaxsiy ma'lumotlarni qabul qilishdan oldin: rasmiy shaxsiy ma'lumotlar siyosati, rozilik, saqlash muddatlari, mas'ul shaxs, audit, server xavfsizligi, zaiflik skaneri va huquqiy muvofiqlikni tasdiqlang.
- Google Sheets/Drive integratsiyasi, email/SMS, parolni o'zgartirish, ko'p admin rollari, vizual sahifa bloklari, avtomatik backup, i18n, ariza holatini xavfsiz tekshirish hali yo'q.
- Universitetning rasmiy nomi, domeni, logosi, telefon/manzili va kontrakt ma'lumotlari egasi tomonidan tasdiqlanishi kerak.

## Sinov
`python tests.py` orqali API smoke testlarni ishga tushiring. Testlar alohida vaqtinchalik papkada ishlaydi.
