# ISFT PRO’ni joylash

**START_ISFT.bat** kompyuterda ishlaydigan nusxani ochadi. GitHub repozitoriysi loyiha kodini saqlaydi. Ushbu sayt arizalar va admin panel uchun Python serveri hamda SQLite bazasini talab qiladi.

## Serverga ko‘chirish

- Python 3.10 yoki yangiroq va yozish mumkin bo‘lgan doimiy disk papkasi kerak.
- `python server.py` standart holatda `127.0.0.1:8000` da ishlaydi. `PORT` orqali portni, `ISFT_HOST` orqali tinglaydigan manzilni belgilash mumkin.
- Tashqi trafikni HTTPS reverse proxy orqali uzating. HTTPS sozlangandan keyin `ISFT_HTTPS=1` bilan sessiya cookie’siga Secure atributini yoqing.
- `isft.db`, `uploads/` va `sheets.local.json` server diskida turadi. Ular uchun zaxira nusxa va ruxsatlarni sozlang. Mahalliy zaxira olishdan oldin serverni to‘xtating.
- Jadvalga ulanish uchun Apps Script’ning `/exec` manziliga internet chiqishi kerak.

Ommaviy qabulni boshlashdan oldin universitet ma’lumotlari, admin kirishi, hosting, zaxira nusxalari va shaxsiy ma’lumotlar bilan ishlash tartibini tasdiqlang. Python’ning standart HTTP serveri bilan berilgan nusxa lokal ish va sinov uchun mo‘ljallangan.

## Render orqali joylash

Render’da **New → Web Service** ni tanlang. GitHub’dagi `tayirovaybek4-code/isft-klon` repozitoriysining `main` bo‘limini ulang. Runtime uchun **Python 3** ni tanlang. Build Command maydoniga `python -m py_compile server.py sheets_sync.py`, Start Command maydoniga `python server.py` yozing. Render bergan `PORT` qiymatini ishlating.

Doimiy disk qo‘shib, uning Mount Path qiymatini `/var/data` qiling. Environment bo‘limiga quyidagi qiymatlarni qo‘ying.

| O‘zgaruvchi | Qiymat |
|---|---|
| `ISFT_HOST` | `0.0.0.0` |
| `ISFT_HTTPS` | `1` |
| `ISFT_DATA_DIR` | `/var/data` |
| `ADMIN_PASSWORD` | Faqat hosting sozlamasida kiritiladigan kamida 12 belgili maxfiy parol |

Sayt ochilganda bosh sahifani va `/admin.html` orqali kirishni tekshiring. Google Sheets ulanishini serverda yoqish uchun Apps Script faollashtirilgach, hosting shell’ida `python server.py --configure-sheets` ni ishga tushiring va xizmatni qayta oching.

[Render Web Services](https://render.com/docs/web-services) · [Doimiy disk](https://render.com/docs/disks)
