# Arizalarni Google Sheets’ga ulash

Bir marta sozlang. Server SQLite bazasiga yozilgan yangi va oldingi arizalarni **Arizalar** varag‘iga yuboradi. Admin panelda holat o‘zgarganda shu ariza qatori yangilanadi.

## 1. Jadval va skript

1. Google Sheets’da **ISFT PRO — Qabul arizalari** jadvalini oching. Tayyor jadval havolasi bo‘lmasa, yangi jadval yarating.
2. Jadval manzilida `/d/` va `/edit` orasidagi qismni nusxalang. Bu jadvalning ID raqami.
3. Jadvalda **Extensions → Apps Script** ni bosing.
4. Loyiha papkasidagi **GoogleSheets.gs** faylini VS Code’da oching. Hammasini nusxalab, Apps Script’dagi **Code.gs** oynasiga qo‘ying. **Save** ni bosing.
5. Apps Script chap menyusida **Project Settings** ni oching. **Script properties → Add script property** orqali `ISFT_SHEET_ID` ni yarating va 2-qadamdagi ID’ni qiymat sifatida kiriting.

## 2. Maxfiy kalit va Web app manzili

1. Kompyuteringizda **GOOGLE_SHEETS.bat** faylini ikki marta bosing. Terminal mavjud kalitni so‘raganda yangi kalit yaratish uchun **Enter** ni bosing.
2. Terminalda chiqqan kalitni Apps Script’dagi **Script properties** bo‘limiga `ISFT_SYNC_SECRET` nomi bilan qo‘shing. **Save script properties** ni bosing.
3. Apps Script’da **Deploy → New deployment** ni bosing. Tur sifatida **Web app** ni tanlang.
4. **Execute as** maydonida **Me**, **Who has access** maydonida **Anyone** ni tanlang. **Deploy** ni bosing va Google so‘ragan jadval ruxsatini o‘z hisobingizdan tasdiqlang.
5. Oxiri `/exec` bo‘lgan **Web app URL** manzilini nusxalab, terminalga qo‘ying va **Enter** ni bosing. Terminal ulanishni tekshirib, mahalliy sozlamani saqlaydi.
6. Sayt ochiq bo‘lsa, terminalda **Ctrl+C** ni bosing. **START_ISFT.bat** bilan qayta ishga tushiring.

**Anyone** sozlamasi Python serveriga Google hisobiga kirmasdan Web app manziliga so‘rov yuborish imkonini beradi. Skript yozishdan oldin maxfiy kalitni tekshiradi. Jadvalning o‘zidagi **Share** sozlamasini **Restricted** holatida qoldiring. Kalitni va `sheets.local.json` faylini o‘zingizda saqlang. Google Workspace hisobida **Anyone** tanlovi ko‘rinmasa, hisobingizdagi Apps Script ruxsatlari kerak bo‘ladi.

## 3. Sinov

1. Saytda bitta sinov arizasini yuboring.
2. **Admin panel → Google Sheets → Holatni yangilash** ni bosing. **Jadvalga yozilgan** soni oshganini tekshiring.
3. Jadvaldagi **Arizalar** varag‘ida shu ariza raqami chiqadi. Admin panelda holatni o‘zgartirib, aynan shu qator yangilanishini tekshiring.
4. Ulanish uzilsa, yozuvlar mahalliy bazada navbatda qoladi. Server taxminan 30 soniyadan keyin qayta urinadi. Server o‘chiq bo‘lsa, yuborish keyingi ishga tushirishda davom etadi.

Ariza holatini **admin paneldan** o‘zgartiring. Jadvalga uzatiladigan ustunlar ariza raqami, vaqt, ism, familiya, otasining ismi, telefon, tug‘ilgan sana, yo‘nalish, ta’lim shakli, rozilik va holat. Texnik **Sinxron ID** va **Versiya** ustunlarini saqlang. Jadvalni saralashda butun qatorlarni birga saralang.

Rasmiy yo‘riqnoma [Google Apps Script Web Apps](https://developers.google.com/apps-script/guides/web).
