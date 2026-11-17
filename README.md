# ISFT PRO — ishlaydigan lokal boshlang‘ich loyiha

Bu loyiha universitet uchun **mahalliy ishlaydigan MVP**: admin login, arizalar, 16 yo‘nalish, e’lon/yangilik/sahifa materiallari, jonli statistika va faoliyat jurnali. Bu **to‘liq ishlab chiqarishga tayyor tizim emas**.

## Windows (PowerShell)
1. ZIP arxivni oching va papkaga kiring.
2. Python 3.10+ o‘rnatilganini tekshiring: `python --version`.
3. **Birinchi marta** xavfsiz parol belgilang (12+ belgi):
   `$env:ADMIN_PASSWORD="BuYergaOzingizningKuchliParolingizniYozing!"`
4. Serverni ishga tushiring: `python server.py`
5. Brauzerda `http://127.0.0.1:8000` ni oching.
6. Admin panelni oching: `http://127.0.0.1:8000/admin.html`. Login: `admin`; parol: serverni birinchi ishga tushirganda belgilagan parolingiz. Endi login oynasi admin sahifasining o‘zida chiqadi.

**Eslatma:** Parol dastlabki ishga tushirishda SQLite bazasiga xesh ko‘rinishida yoziladi. Keyingi ishga tushirishda `ADMIN_PASSWORD` o‘zgarsa ham eski parol saqlanadi. Ma’lumotlar `isft.db` faylida turadi; zaxira nusxa uchun serverni to‘xtatib, faylni xavfsiz joyga ko‘chiring. Ma’lumotlarni tozalash uchun bazani o‘chirish barcha arizalarni yo‘qotadi.

## Hozir ishlaydigan imkoniyatlar
- Saytdan ariza yuborish, SQLite bazaga saqlash va avtomatik hisoblash.
- 16 yo‘nalish va ularni admin orqali qo‘shish, tahrirlash, yashirish, o‘chirish.
- E’lon, yangilik, sahifa materiallarini qo‘shish, tahrirlash, chop etish, o‘chirish.
- Admin login (PBKDF2), HTTP-only cookie, CSRF tekshiruvi, server tarafida ruxsat nazorati.
- Dashboard, 30 kunlik grafik, yo‘nalishlar reytingi, ariza holatini o‘zgartirish, qidiruv, faoliyat jurnali.

## Ishlab chiqarishga chiqarishdan oldin majburiy ishlar
- HTTPS va reverse proxy, persistent session storage, login urinishlarini cheklash, xavfsizlik auditi, avtomatik testlar.
- Fayl yuklash va media kutubxona; Google Sheets/Drive integratsiyasi; sahifa bloklarini vizual boshqarish; rollar va parolni tiklash; to‘liq ko‘p tillilik.
- Ariza raqami orqali xavfsiz tekshirish, SMS tasdiqlash, ma’lumotlarni saqlash siyosati va huquqiy rozilik.
- Rasmiy ISFT ma’lumotlari, kontrakt narxlari, ta’lim shakllari va domenni tasdiqlash.
- Hozirgi sahifa ko‘rinishlari oddiy prototip; dizayn maketidagi barcha tugmalar hali to‘liq amalga oshirilmagan.

**Muhim:** Lokal serverni internetga bevosita ochmang; foydalanuvchilarning haqiqiy pasport ma’lumotlarini sinov tizimiga kiritmang. Dashboarddagi sonlar real saqlangan arizalardan hisoblanadi; dastlab 0 bo‘ladi.

## 2026-11-05 — yangilangan PRO versiya
- **Yangi:** saytdagi menyu tugmalarini admin paneldan qo‘shish, tahrirlash, o‘chirish va tartiblash.
- **Yangi:** bosh sahifa sarlavhasi, izohi, aloqa ma’lumotlari va footer matnini admin paneldan tahrirlash.
- **Yangi:** 3 MB gacha PNG/JPEG/WEBP/GIF media kutubxonasi, havolani nusxalash va o‘chirish.
- **Yangi:** `about.html`, `contact.html`, `program-detail.html` alohida sahifalari.
- **Xavfsizlik:** SQLite-da persistent sessiya, login urinishlarini cheklash, CSP va HTTP security headerlar.
- **Sinov:** `python tests.py` — API integratsiya tekshiruvi.
- **Muhim:** ommaviy ishga tushirishdan oldin `DEPLOYMENT.md` ni o‘qing; hozirgi loyiha production sertifikatiga ega emas. Real foydalanuvchi ma’lumotlarini ommaviy yig‘ishni hali boshlamang.
