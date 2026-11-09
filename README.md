# ISFT PRO

ISFT uslubidagi qabul sayti va admin panel. Yo‘nalishlar, arizalar, yangiliklar, sahifa matnlari, menyu, media va statistika bir loyihada boshqariladi. SQLite bazasi hamda Google Sheets bilan sinxronlash Python standart kutubxonasi orqali ishlaydi.

## Windows’da ishga tushirish

1. ZIP faylni o‘ng tugma bilan bosing va **Extract All… → Extract** ni tanlang.
2. Ajratilgan **isft_pro** papkasiga kiring. Kompyuterda **Python 3.10 yoki yangiroq** bo‘lishi kerak.
3. **START_ISFT.bat** faylini ikki marta bosing.
4. Birinchi ishga tushirishda kamida 12 belgili admin paroli yozing. **Enter** ni bosing va parolni yana kiriting. Terminal parol belgilarini ekranda yashiradi.
5. Brauzerda [bosh sahifa](http://127.0.0.1:8000/) ochiladi. Pastdagi **Admin panel** havolasini bosing yoki [admin panelni](http://127.0.0.1:8000/admin.html) oching. Login **admin**, parol esa 4-qadamda belgilagan parolingiz.
6. Sayt ishlashi uchun terminal oynasi ochiq turishi kerak. To‘xtatish uchun terminalda **Ctrl+C** ni bosing.

VS Code orqali ochish uchun **File → Open Folder** da `server.py` turgan papkani tanlang. **Terminal → New Terminal** da `python server.py` ni yozing. Port band bo‘lsa, PowerShell’da `$env:PORT="8001"` ni yozib, serverni qayta oching.

## Qabulni tekshirish

1. Saytdagi **Ariza topshirish** sahifasidan sinov arizasini yuboring. Ekranda ariza raqami chiqadi.
2. **Admin panel → Arizalar** da shu raqamni qidiring. Ismni bosib batafsil ma’lumotni oching.
3. Holatni tanlab **Saqlash** ni bosing. **Qabul qilingan** holatidagi ariza **Talabalar** ro‘yxatida ham chiqadi.
4. **Google Sheets** bo‘limida yuborilgan va navbatdagi yozuvlar sonini ko‘ring. Bir martalik ulash qadamlari [GOOGLE_SHEETS.md](GOOGLE_SHEETS.md) faylida.

Yo‘nalishlar, sayt nomi, sarlavha va aloqa ma’lumotlarini admin paneldan tahrirlash mumkin. Bosh sahifada faol yo‘nalishlar hamda chop etilgan so‘nggi uchta yangilik yoki e’lon ko‘rinadi. **Sahifalar** bo‘limidan matnni **Biz haqimizda** yoki **Aloqa** sahifasiga joylang.

## Mavjud bazani ko‘chirish

Agar eski nusxada arizalar yoki sozlamalar bo‘lsa, ikkala serverni to‘xtating. Eski papkadan `isft.db` va mavjud bo‘lsa `uploads/` papkasini yangi **isft_pro** papkasiga ko‘chiring. Eski papkani zaxira sifatida saqlang. Server birinchi ochilishda bazani avtomatik moslashtiradi va avvalgi admin parolini ishlatadi.

`isft.db` va `sheets.local.json` ishga tushirish va Google’ni ulash vaqtida yaratiladi. Ularni kod bilan birga GitHub’ga joylamang. Testlar alohida vaqtinchalik bazada ishlaydi. Ishga tushirish buyrug‘i `python tests.py`.

Lokal manzil shu kompyuterda ishlaydi. Internetdagi hosting uchun [DEPLOYMENT.md](DEPLOYMENT.md) faylini ko‘ring.
