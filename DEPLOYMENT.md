# ISFT PRO’ni joylash

**START_ISFT.bat** kompyuterda ishlaydigan nusxani ochadi. GitHub repozitoriysi loyiha kodini saqlaydi. Ushbu sayt arizalar va admin panel uchun Python serveri hamda SQLite bazasini talab qiladi.

## Serverga ko‘chirish

- Python 3.10 yoki yangiroq va yozish mumkin bo‘lgan doimiy disk papkasi kerak.
- `python server.py` standart holatda `127.0.0.1:8000` da ishlaydi. `PORT` orqali portni, `ISFT_HOST` orqali tinglaydigan manzilni belgilash mumkin.
- Tashqi trafikni HTTPS reverse proxy orqali uzating. HTTPS sozlangandan keyin `ISFT_HTTPS=1` bilan sessiya cookie’siga Secure atributini yoqing.
- `isft.db`, `uploads/` va `sheets.local.json` server diskida turadi. Ular uchun zaxira nusxa va ruxsatlarni sozlang. Mahalliy zaxira olishdan oldin serverni to‘xtating.
- Jadvalga ulanish uchun Apps Script’ning `/exec` manziliga internet chiqishi kerak.

Ommaviy qabulni boshlashdan oldin universitet ma’lumotlari, admin kirishi, hosting, zaxira nusxalari va shaxsiy ma’lumotlar bilan ishlash tartibini tasdiqlang. Python’ning standart HTTP serveri bilan berilgan nusxa lokal ish va sinov uchun mo‘ljallangan.
