# Onlayn qabul va imtihonlar

Saytning asosiy sahifasi `/`, admin panel `/admin.html`, abituriyent kabineti `/exam.html`.

## Ish tartibi

1. Abituriyent Google orqali kiradi. Ism va tasdiqlangan pochta bazaga saqlanadi.
2. Kabinetda yo‘nalishni tanlab, testga ariza beradi. Oddiy qabul arizasi ham shu testga arizani yaratadi.
3. Administrator **Testga arizalar** bo‘limidan ruxsat beradi.
4. Administrator **Test va qabul sozlamalari** bo‘limida savollarni tekshiradi va testni ochadi.
5. Abituriyent **Imtihonni boshlash** tugmasini bosganda serverda 90 daqiqalik hisob boshlanadi. Qayta kirish yoki sahifani yangilash vaqtni uzaytirmaydi.
6. Javoblar tanlanganda serverga saqlanadi. Internet uzilganda saqlanmagan javoblar yo‘qolishi mumkin. Vaqt tugaganda serverda saqlangan javoblar baholanadi.
7. Natija va tabrik yoki dalda matni darhol saytda ko‘rinadi. Admin **Test topshirganlar → Ko‘rish** orqali javoblar va ballarni ko‘radi.

## Savollar va qabul

16 ta boshlang‘ich yo‘nalishning har biri uchun 28 ta tahrirlanadigan savol mavjud. Har to‘plamda 14 ta soha va unga yaqin fan savoli, 14 ta matematika, mantiq va axborotni baholash savoli bor. Ayrim savollar yaqin yo‘nalishlarda takrorlanadi. Savollar boshlang‘ich qoralama sifatida tayyorlangan, rasmiy universitet test banki emas. Testni ochishdan oldin mas’ul xodim matn, javoblar va qabul mezonini ko‘rib chiqadi.

Boshlang‘ich o‘tish chegarasi 60%. 28 savoldan 17 tasi to‘g‘ri bo‘lsa o‘tadi. Har savol teng ball. Administrator foizni o‘zgartirishi mumkin. Boshlangan imtihon o‘zining savollar va o‘tish bali nusxasini saqlaydi.

Har abituriyent har yo‘nalish imtihonini bir marta topshiradi. Boshlanmagan ariza uchun ruxsatni o‘zgartirish mumkin. Test boshlanganidan keyin ruxsat bekor qilinmaydi.

**Qabul ochiq** belgisini olib tashlash yangi arizalarni yopadi. **Joylar soni** kutilayotgan va ruxsat berilgan test arizalariga cheklov qo‘yadi. Rad etilgan ariza joyni bo‘shatadi. Oldin ruxsat olgan abituriyent qabul yopilgandan keyin ham testini davom ettiradi. Yo‘nalishni yashirish va qabulni yopish alohida amallar.

## Google orqali kirishni ulash

Google Cloud Console’da OAuth uchun Web application client yarating va rozilik ekranini sozlang. Authorized redirect URI saytning aniq manzili bilan `/auth/google/callback` bo‘lsin. Lokal sinov uchun `http://127.0.0.1:8000/auth/google/callback` ishlatiladi. Ishlayotgan ommaviy sayt uchun HTTPS zarur.

Server ishlaydigan muhitga quyidagi qiymatlarni kiriting.

```text
GOOGLE_CLIENT_ID=<Google bergan Client ID>
GOOGLE_CLIENT_SECRET=<Google bergan maxfiy kalit>
GOOGLE_REDIRECT_URI=https://sizning-domainingiz/auth/google/callback
ISFT_HTTPS=1
```

Maxfiy kalitni kodga yoki Git’ga yozmang. Serverni qayta ishga tushiring. OAuth ilovasi Google’da test holatida bo‘lsa, faqat ruxsat berilgan test foydalanuvchilari kira oladi. Haqiqiy ulanishni hisob bilan sinash uchun tegishli Google sozlamalari talab qilinadi.

Google OAuth oqimi authorization code, PKCE, bir martalik browser state va server orqali userinfo tekshiruvini ishlatadi. Admin login alohida qoladi.

Rasmiy qo‘llanma — https://developers.google.com/identity/openid-connect/openid-connect

## Google Drive ichidagi jadvallar

`GOOGLE_SHEETS.md` bo‘yicha Google Sheets va Apps Script’ni ulang. Yangilangan `GoogleSheets.gs` kodini Apps Script’ga qo‘ying va yangi deployment versiyasini chiqaring. `GOOGLE_SHEETS.bat` bilan ulanishni saqlang. Server qayta ishga tushgach ma’lumotlar quyidagi alohida varaqlarga yoziladi.

- **Ro‘yxatdan o‘tganlar** — Google orqali kirganlar.
- **Testga arizalar** — yo‘nalish va ruxsat holati.
- **Test topshirganlar** — ball, natija va berilgan javoblar.
- **Qabul arizalari** — to‘liq qabul formasi.

Google Sheets fayli tanlangan Google hisobining Drive’ida turadi. Saytga kirgan har bir abituriyentning shaxsiy Drive’iga yozilmaydi. Google ulanmaguncha ma’lumotlar lokal bazada navbatda saqlanadi. Xatoda avtomatik qayta uriniladi. Bir yozuvning qayta yuborilishi jadvalda nusxa yaratmaydi. Ulanish holati adminning ro‘yxat va natijalar bo‘limida ko‘rinadi.

## Yangilik va reklama

Adminning **E’lonlar va yangiliklar → Yangi material** bo‘limida **Yangilik**, **E’lon** yoki **Reklama** turini tanlang. Chop etilgan reklama bosh sahifadagi alohida banner joyiga, yangilik va e’lonlar esa yangiliklar bo‘limiga chiqadi. Hozir reklama sarlavha va matn ko‘rinishida kiritiladi.

## Tekshirish

```powershell
python -B tests.py
```

Testlar alohida vaqtinchalik baza va test hisobidan foydalanadi. Haqiqiy Google hisobiga kirmaydi va tashqi jadvalga ma’lumot yubormaydi.
