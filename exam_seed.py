"""Editable draft entrance questions. First option is the key before rotation."""

COMMON = '''
200 ning 15 foizi nechaga teng?|30|15|20|45
3x + 5 = 20 tenglamada x nechaga teng?|5|3|7|15
2, 4, 8, 16 ketma-ketlikdagi keyingi son qaysi?|32|18|24|30
Bir xil ish unumida 4 ishchi ishni 6 kunda bajarsa, 8 ishchi necha kunda bajaradi?|3|12|6|2
Axborotning ishonchliligini tekshirishning eng yaxshi usuli qaysi?|Bir nechta mustaqil ishonchli manbani solishtirish|Faqat sarlavhani o‘qish|Eng ko‘p ulashilgan xabarga ishonish|Muallifning rasmini tekshirish
12, 18 va 24 sonlarining o‘rtacha arifmetigi nechaga teng?|18|16|20|54
Narx 80 000 so‘mdan 100 000 so‘mga oshdi. O‘sish necha foiz?|25%|20%|80%|125%
Qutida 3 ta qizil va 2 ta ko‘k shar bor. Tasodifan olingan sharning ko‘k bo‘lish ehtimoli qancha?|2/5|3/5|1/5|1/2
To‘g‘ri to‘rtburchak tomonlari 6 va 4 metr. Uning yuzi qancha?|24 kvadrat metr|20 kvadrat metr|10 kvadrat metr|12 kvadrat metr
1,5 soat necha daqiqaga teng?|90|60|75|150
250 ta kitobning 2/5 qismi tarqatildi. Nechta kitob qoldi?|150|100|200|50
Barcha A lar B. Hech bir B C emas. Qaysi xulosa to‘g‘ri?|Hech bir A C emas|Barcha C lar A|Barcha B lar A|A lar haqida hech qanday xulosa yo‘q
Matnda keltirilgan faktni fikrdan ajratadigan asosiy belgi qaysi?|Fakt dalillar bilan tekshirilishi mumkin|Fakt doim yoqimli bo‘ladi|Fikr doim raqam bilan yoziladi|Fakt faqat uzun gap bo‘ladi
Mahsulot 120 000 so‘m. 25% chegirmadan keyingi narx qancha?|90 000 so‘m|95 000 so‘m|100 000 so‘m|30 000 so‘m
'''

SUBJECTS = {
'Axborot tizimlari va texnologiyalari': '''
Algoritm nima?|Masalani yechish uchun aniq amallar ketma-ketligi|Faqat kompyuter qurilmasi|Tasodifiy buyruqlar|Internet tezligi
Ma’lumotlar bazasida birlamchi kalitning vazifasi nima?|Har bir yozuvni yagona aniqlash|Matn rangini belgilash|Internetni tezlashtirish|Faylni siqish
RAM qanday xotira?|Elektr uzilganda ma’lumotlari yo‘qoladigan tezkor xotira|Doimiy optik xotira|Faqat tashqi xotira|Bosma xotira
HTTP asosan nima uchun ishlatiladi?|Veb resurslarni uzatish|Elektr kuchlanishini o‘lchash|Protsessorni sovitish|Rasmni qog‘ozga chiqarish
Ikkilik sanoq tizimidagi 101 soni o‘nlikda nechaga teng?|5|3|4|6
''',
'Iqtisodiyot': '''
Resurslar cheklanganligi qanday muammoni keltirib chiqaradi?|Muqobil variantlar orasida tanlov qilish zaruratini|Barcha ehtiyojlarning avtomatik qondirilishini|Narxlarning doim nol bo‘lishini|Tanlovning yo‘qolishini
Talab qonuniga ko‘ra, boshqa shartlar o‘zgarmaganda narx oshsa nima bo‘ladi?|Talab miqdori kamayadi|Talab miqdori doim oshadi|Taklif yo‘qoladi|Daromad majburan ortadi
Muqobil xarajat nima?|Tanlov tufayli voz kechilgan eng yaxshi imkoniyat qiymati|Faqat pul bilan to‘langan xarajat|O‘tgan yildagi barcha xarajat|Faqat soliq summasi
Inflyatsiya nimani anglatadi?|Narxlar umumiy darajasining oshishini|Bitta mahsulot narxining har qanday o‘zgarishini|Ishlab chiqarishning doim oshishini|Valyutaning yo‘qolishini
Foyda qanday hisoblanadi?|Jami daromaddan jami xarajat ayiriladi|Daromad va xarajat qo‘shiladi|Faqat ish haqi olinadi|Daromad xarajatlarga tenglashtiriladi
''',
'Marketing': '''
Bozor segmentatsiyasi nima?|Xaridorlarni o‘xshash ehtiyojlariga ko‘ra guruhlash|Barcha xaridorga bir xil ehtiyoj belgilash|Faqat reklama rangini tanlash|Mahsulotni omborga joylash
Marketing tadqiqotining asosiy vazifasi nima?|Qarorlar uchun bozor haqidagi ma’lumotlarni yig‘ish va tahlil qilish|Faqat shior yozish|Raqobatchi mahsulotini nusxalash|Faqat narxni oshirish
Marketingdagi 4P tarkibiga qaysi to‘plam kiradi?|Mahsulot, narx, tarqatish, ilgari surish|Foyda, soliq, kredit, qarz|Xodim, rahbar, hisobchi, mijoz|Reja, buyruq, nazorat, jarima
Maqsadli auditoriya nima?|Mahsulot taklifi yo‘naltirilgan xaridorlar guruhi|Korxonaning barcha jihozlari|Faqat reklama mualliflari|Ombor zaxiralari
100 ta tashrifdan 5 ta xarid bo‘lsa, konversiya necha foiz?|5%|20%|50%|95%
''',
'Bank ishi': '''
Depozit nima?|Bankka saqlash shartlari asosida qo‘yilgan mablag‘|Bank binosi|Qaytarilmaydigan jarima|Faqat qog‘oz pul turi
Kreditning asosiy xususiyati qaysi?|Mablag‘ni shartnoma bo‘yicha qaytarish majburiyati|Har doim bepul berilishi|Hech qanday muddati bo‘lmasligi|Faqat sovg‘a bo‘lishi
Diversifikatsiya nima?|Riskni kamaytirish uchun mablag‘larni turli yo‘nalishlarga taqsimlash|Barcha mablag‘ni bitta aktivga qo‘yish|Barcha aktivni yashirish|Xarajatlarni hisoblamaslik
Likvidlik nimani bildiradi?|Aktivni katta yo‘qotishsiz pulga aylantirish imkoniyatini|Korxona nomini|Faqat kredit muddatini|Mahsulot og‘irligini
1 000 000 so‘mga yillik oddiy 10% foiz hisoblansa, bir yillik foiz qancha?|100 000 so‘m|10 000 so‘m|1 100 000 so‘m|900 000 so‘m
''',
'Axborot xavfsizligi': '''
Fishing nima?|Soxta xabar yoki sahifa orqali maxfiy ma’lumotni qo‘lga kiritish|Faylni zaxiralash|Tarmoqni qonuniy tezlashtirish|Parolni shifrlash
Ikki bosqichli autentifikatsiya nimani yaxshilaydi?|Hisobga kirish himoyasini|Monitor yorqinligini|Fayl hajmini|Printer tezligini
Eng kam vakolat tamoyili nimani anglatadi?|Faqat vazifaga zarur huquqlarni berish|Hammaga administrator huquqi berish|Parollarni umumiy qilish|Nazoratni olib tashlash
Zaxira nusxaning asosiy maqsadi nima?|Ma’lumot yo‘qolganda tiklash|Parolni ommaga e’lon qilish|Fayl nomini o‘zgartirish|Reklama tarqatish
Qaysi amal parol xavfsizligini yaxshilaydi?|Har xizmat uchun uzun va alohida parol ishlatish|Barcha joyda bir xil qisqa parol ishlatish|Parolni ochiq xabarda yuborish|Tug‘ilgan yilni yagona parol qilish
''',
'Xalqaro munosabatlar': '''
Diplomatiyaning asosiy vositasi qaysi?|Muzokara va muloqot|Faqat harbiy harakat|Faqat savdo taqiqi|Ichki buxgalteriya
Davlat suvereniteti nimani bildiradi?|Davlatning ichki va tashqi masalalarda mustaqilligini|Boshqa davlatga to‘liq qaramlikni|Faqat hudud maydonini|Faqat aholi sonini
Ikki tomonlama shartnoma nechta tomon o‘rtasida tuziladi?|Ikki|Uch|To‘rt|Kamida o‘n
Xalqaro tashkilot nima?|Umumiy maqsadlar uchun davlatlar yoki boshqa subyektlar tuzgan tuzilma|Faqat bitta shaxs kundaligi|Har qanday mahalliy do‘kon|Faqat oilaviy yig‘ilish
Nizoni tinch hal qilishga qaysi usul misol bo‘ladi?|Vositachilik|Tahdidni kuchaytirish|Muloqotni butunlay rad etish|Dalillarni yashirish
''',
'Menejment': '''
Rejalashtirishning vazifasi nima?|Maqsad va unga erishish yo‘llarini belgilash|Faqat bajarilgan ishni jazolash|Barcha qarorni tasodifiy qilish|Hisobotlarni yo‘qotish
Delegatsiya nima?|Vazifa va tegishli vakolatni xodimga topshirish|Barcha vazifani rahbarning o‘zi bajarishi|Jamoani tarqatish|Rejani bekor qilish
SMART maqsadga qaysi misol mos?|Keyingi 30 kunda 20 ta mijoz so‘rovini tahlil qilish|Yaxshi ishlash|Qachondir o‘sish|Hamma narsani yaxshilash
Samarali qayta aloqa qanday bo‘ladi?|Aniq xatti-harakat va yaxshilash yo‘liga asoslanadi|Faqat shaxsni haqorat qiladi|Dalilsiz ayblaydi|Faqat mish-mishga asoslanadi
Nazorat funksiyasi nimani o‘z ichiga oladi?|Natijani reja bilan solishtirish|Maqsadni yashirish|Barcha xodimni almashtirish|Faqat bayram tashkil qilish
''',
'Biznes va menejment': '''
Biznes model nimani tushuntiradi?|Korxona qanday qiymat yaratishi va daromad olishini|Faqat bino rangini|Faqat xodim kiyimini|Faqat logotip shaklini
Zararsizlik nuqtasida qanday holat kuzatiladi?|Jami daromad jami xarajatga teng|Daromad nol bo‘lishi shart|Xarajat nol bo‘lishi shart|Foyda maksimal bo‘ladi
Doimiy xarajatga qaysi misol mos?|Shartnomada belgilangan oylik ijara haqi|Har sotilgan mahsulot uchun qadoq|Har birlik uchun xomashyo|Sotuvdan foizli komissiya
Mijoz uchun qiymat taklifi nimani bildiradi?|Mahsulot hal qiladigan muammo va beradigan foydani|Faqat rahbarning yoshini|Faqat soliq raqamini|Ombor manzilini
SWOT tahlilidagi kuchli tomon qanday omil?|Ichki ijobiy omil|Tashqi salbiy omil|Faqat tasodifiy hodisa|Faqat valyuta kursi
''',
'Moliya sohasida boshqaruv': '''
Budjet nima?|Kutilayotgan daromad va xarajatlar rejasi|Faqat o'tgan qarzlar ro‘yxati|Faqat mahsulot nomi|Faqat kassa apparati
Pul oqimi nimani ifodalaydi?|Mablag‘larning kirimi va chiqimini|Faqat hisobdagi foydani|Faqat aktiv nomlarini|Faqat narxlar ro‘yxatini
Pulning vaqt qiymati g‘oyasi nimani anglatadi?|Bugungi mablag‘ va kelajakdagi teng summa qiymati farq qilishi mumkin|Pul hech qachon qiymatga ega emas|Har qanday investitsiya kafolatli|Vaqt xarajatlarga ta’sir qilmaydi
Risk va kutilayotgan daromad odatda qanday bog‘liq?|Yuqori kutilayotgan daromad ko‘proq risk bilan bog‘liq bo‘lishi mumkin|Yuqori daromad doim risksiz|Risk mavjud emas|Daromad doim bir xil
Sof aylanma kapital qanday hisoblanadi?|Joriy aktivlar minus joriy majburiyatlar|Uzoq muddatli aktivlar plus foyda|Faqat naqd pul|Faqat asosiy vositalar
''',
'Buxgalteriya hisobi va moliya': '''
Asosiy buxgalteriya tenglamasi qaysi?|Aktivlar = majburiyatlar + kapital|Aktivlar = faqat daromad|Kapital = xarajatlar + savdo|Majburiyatlar = faqat pul
Ikkiyoqlama yozuv nimani anglatadi?|Operatsiyani teng summada debet va kreditda aks ettirish|Har hujjatni ikki marta chop etish|Har to‘lovni ikki marta amalga oshirish|Faqat aktivlarni sanash
Debitorlik qarzi nima?|Boshqalarning korxonaga to‘lashi kerak bo‘lgan qarzi|Korxonaning bankka barcha qarzi|Korxona kapitali|Faqat ish haqi xarajati
Amortizatsiya nima?|Aktiv qiymatini foydali xizmat davriga taqsimlash|Aktivni doim bepul olish|Har oy aktivni qayta sotish|Faqat soliqqa jarima
Moliyaviy holat hisoboti nimani ko‘rsatadi?|Muayyan sanadagi aktivlar, majburiyatlar va kapitalni|Faqat reklama rejasini|Faqat xodimlarning yoshini|Faqat kelajakdagi kafolatli foydani
''',
'Xorijiy til va adabiyoti': '''
Choose the correct sentence.|She goes to school every day.|She go to school every day.|She going to school every day.|She gone to school every day.
Choose the past tense of “write”.|Wrote|Written|Writing|Writes
Which word is a synonym of “begin”?|Start|Finish|Forget|Close
A metaphor is best described as what?|A comparison that describes one thing as another|A list of dates|An exact quotation only|A spelling rule
Choose the correct article: “She is ___ engineer.”|an|a|the only|no any
''',
'Maktabgacha ta’lim': '''
Maktabgacha yoshda o‘rganishning muhim usuli qaysi?|Maqsadli o‘yin va amaliy faoliyat|Faqat uzun ma’ruza|Faqat baho bilan qo‘rqitish|Harakatni butunlay cheklash
Mayda motorikani rivojlantiradigan mashg‘ulot qaysi?|Yoshga mos plastilin bilan shakl yasash|Faqat yugurish|Faqat tinglash|Faqat sakrash
Bola yangi vazifada qiynalsa, tarbiyachi nima qilishi ma’qul?|Yordamni bosqichma-bosqich berishi|Boshqalar oldida kamsitishi|Urinishni taqiqlashi|Darhol jazolashi
Inklyuziv ta’lim nimaga intiladi?|Turli ehtiyojli bolalarning ishtiroki uchun sharoit yaratishga|Faqat eng tez o‘rganuvchilarni tanlashga|Bolalarni doim ajratishga|Individual ehtiyojlarni inkor qilishga
Bolalar nutqini rivojlantirishga qaysi faoliyat yordam beradi?|Rasm asosida suhbat va hikoya tuzish|Muloqotni taqiqlash|Faqat jim o‘tirish|Har savolni e’tiborsiz qoldirish
''',
'Boshlang‘ich ta’lim': '''
Formativ baholashning maqsadi nima?|O‘rganish jarayonida qayta aloqa berish|Faqat yakuniy reyting tuzish|Faqat jazolash|Davomatni almashtirish
O‘qib tushunishni tekshirishga qaysi savol mos?|Matndagi qahramon nima sababdan shunday qaror qildi?|Matn nechta sahifada bosilgan?|Kitob muqovasi qanday rangda?|Kitobning og‘irligi qancha?
Kasrni dastlab tushuntirish uchun qaysi usul qulay?|Butunni teng qismlarga ajratib ko‘rsatish|Faqat qoidani yodlatish|Belgilarni izohsiz yozish|Mavzuni tashlab ketish
Differensial ta’lim nima?|Topshiriqlarni o‘quvchilar ehtiyojiga moslashtirish|Hammaga izohsiz bir xil murakkab vazifa berish|Faqat kuchli o‘quvchiga dars berish|Baholashni butunlay bekor qilish
Xatoga konstruktiv munosabat qaysi?|Xato sababini birga aniqlab, qayta urinishga yo‘l berish|O‘quvchini masxara qilish|Savol berishni taqiqlash|Faqat bahoni pasaytirish
''',
'Pedagogika': '''
Didaktika nimani o‘rganadi?|Ta’lim va o‘qitish nazariyasini|Faqat maktab binolarini|Faqat sport musobaqalarini|Faqat moliyaviy hisobni
O‘quv maqsadi qanday yozilishi ma’qul?|Kuzatiladigan natija orqali|Faqat mavzu nomi bilan|Faqat dars sanasi bilan|Faqat o‘qituvchi kayfiyati bilan
Faol o‘rganishga qaysi misol mos?|Muammoni guruhda tahlil qilish va yechimni asoslash|Faqat izohsiz ko‘chirish|Butun dars sukut saqlash|Savollarni taqiqlash
Baholash mezoni nimaga xizmat qiladi?|Natijani aniq talablar bo‘yicha baholashga|Tasodifiy baho qo‘yishga|Faqat davomatni tekshirishga|O‘quvchilarni taqqoslab kamsitishga
Refleksiya nima?|O‘z o‘rganishi va faoliyatini tahlil qilish|Faqat javobni ko‘chirish|Faqat dam olish|Natijalarni yashirish
''',
'Psixologiya': '''
Empatiya nima?|Boshqa insonning his-tuyg‘ularini tushunishga intilish|Boshqani doim ayblash|Faqat o‘z fikrini takrorlash|Har doim maslahat berish majburiyati
Diqqat nima?|Psixik faoliyatning muayyan obyektga yo‘naltirilishi|Faqat uzoq muddatli xotira|Faqat uyqu holati|Faqat nutq tezligi
Ilmiy tadqiqotda gipoteza nima?|Tekshirish mumkin bo‘lgan taxmin|Isbotsiz yakuniy haqiqat|Faqat kuzatuv daftari|Faqat tasodifiy so‘z
Korrelyatsiya haqida qaysi fikr to‘g‘ri?|Bog‘liqlikning o‘zi sabab-oqibatni isbotlamaydi|Har bir bog‘liqlik sababni isbotlaydi|Korrelyatsiya hech qachon o‘lchanmaydi|Korrelyatsiya faqat bitta hodisani bildiradi
Tadqiqotdagi ongli rozilik nimani talab qiladi?|Ishtirokchi maqsad va shartlarni tushunib ixtiyoriy rozi bo‘lishini|Ishtirokchini majburlashni|Maqsadni doim yashirishni|Natijani oldindan belgilashni
''',
'Filologiya va tillarni o‘qitish (Ingliz tili)': '''
Which sentence uses the present perfect correctly?|I have finished my homework.|I has finished my homework.|I have finish my homework.|I am finish my homework.
Which word is an adjective?|Beautiful|Quickly|Run|Happiness
Choose the correct passive form of “They build houses.”|Houses are built.|Houses is build.|Houses built they.|Houses are builded.
Tilshunoslikda fonetika nimani o‘rganadi?|Nutq tovushlarini|Faqat gap ma’nosini|Faqat lug‘at tartibini|Faqat badiiy janrlarni
Communicative language teaching primarily emphasizes what?|Meaningful interaction in the target language|Only copying grammar rules|Avoiding speaking|Only translating word lists
'''
}

RELATED = {
 'Axborot tizimlari va texnologiyalari':'Axborot xavfsizligi',
 'Iqtisodiyot':'Biznes va menejment', 'Marketing':'Biznes va menejment',
 'Bank ishi':'Moliya sohasida boshqaruv', 'Axborot xavfsizligi':'Axborot tizimlari va texnologiyalari',
 'Xalqaro munosabatlar':'Iqtisodiyot', 'Menejment':'Biznes va menejment',
 'Biznes va menejment':'Menejment', 'Moliya sohasida boshqaruv':'Buxgalteriya hisobi va moliya',
 'Buxgalteriya hisobi va moliya':'Moliya sohasida boshqaruv',
 'Xorijiy til va adabiyoti':'Filologiya va tillarni o‘qitish (Ingliz tili)',
 'Maktabgacha ta’lim':'Pedagogika', 'Boshlang‘ich ta’lim':'Pedagogika',
 'Pedagogika':'Boshlang‘ich ta’lim', 'Psixologiya':'Pedagogika',
 'Filologiya va tillarni o‘qitish (Ingliz tili)':'Xorijiy til va adabiyoti',
}

EXTRA = {
'Axborot tizimlari va texnologiyalari': '''
Ma’lumotlar bazasida SQL SELECT operatori nima qiladi?|Ma’lumotlarni o‘qib oladi|Monitorni o‘chiradi|Elektr tarmog‘ini tekshiradi|Faqat faylni siqadi
Operatsion tizimning vazifasi qaysi?|Qurilma resurslari va dasturlar ishini boshqarish|Faqat veb sahifa chizish|Faqat reklama ko‘rsatish|Faqat diskni almashtirish
IP manzil nima uchun kerak?|Tarmoqdagi qurilma yoki interfeysni manzillash|Klaviatura tilini belgilash|Ekran rangini o‘zgartirish|Faylni chop etish
Ma’lumotni saralash nima?|Yozuvlarni belgilangan mezon bo‘yicha tartiblash|Barcha yozuvlarni o‘chirish|Faqat nusxalash|Ma’lumotni yashirish
''',
'Iqtisodiyot': '''
Taklif qonuniga ko‘ra, boshqa shartlar o‘zgarmaganda narx oshsa nima bo‘ladi?|Taklif miqdori ortishga moyil bo‘ladi|Taklif doim nolga tushadi|Talab cheksiz bo‘ladi|Ishlab chiqarish taqiqlanadi
Bozor muvozanati qachon yuzaga keladi?|Talab miqdori taklif miqdoriga teng bo‘lganda|Narx nol bo‘lganda|Barcha xaridor bir xil bo‘lganda|Ishlab chiqaruvchi qolmaganda
Mehnat unumdorligi qaysi ko‘rsatkich bilan ifodalanishi mumkin?|Bir ish soatida ishlab chiqarilgan mahsulot soni|Korxona nomi uzunligi|Faqat xodimlar tug‘ilgan yili|Reklama rangi
Jamoat ne’matiga odatiy misol qaysi?|Ko‘cha yoritilishi|Shaxsiy sendvich|Bitta odamning oyoq kiyimi|Shaxsiy ruchka
''',
'Marketing': '''
Brendga sodiqlik nimani bildiradi?|Xaridorning brendni qayta tanlashga moyilligini|Xaridorning doim do‘kon almashtirishini|Faqat reklama hajmini|Faqat logotip o‘lchamini
A/B sinovning maqsadi nima?|Ikki variant natijasini taqqoslash|Barcha variantni bir xil deb olish|Natijani o‘lchamaslik|Faqat nomni almashtirish
Pozitsiyalash nima?|Mahsulotning xaridor ongidagi o‘ziga xos o‘rnini belgilash|Mahsulotni faqat tokchaga qo‘yish|Barcha narxni bir xil qilish|Buxgalteriya yozuvi
Mijoz fikrini olishning bevosita usuli qaysi?|So‘rovnoma yoki intervyu|Faqat rahbar taxmini|Faqat raqobatchi logotipi|Faqat ombor hajmi
''',
'Bank ishi': '''
Kredit riski nimani anglatadi?|Qarz oluvchi majburiyatini bajarmaslik ehtimolini|Bankning bezak tanlashini|Faqat xodim dam olishini|Pulning rangini
Garovning vazifasi nima?|Majburiyat bajarilishini ta’minlashga xizmat qilish|Qarzni avtomatik sovg‘aga aylantirish|Foizni doim nol qilish|Shartnomani yo‘q qilish
Oddiy va murakkab foizning farqi nimada?|Murakkab foizda oldingi foizga ham foiz hisoblanadi|Oddiy foizda hech qanday summa yo‘q|Murakkab foiz doim manfiy|Ikkisida muddat ishlatilmaydi
Mijozni identifikatsiya qilish nimaga xizmat qiladi?|Mijoz shaxsini aniqlashga|Faqat reklama yuborishga|Monitorni sozlashga|Bank logotipini tanlashga
''',
'Axborot xavfsizligi': '''
Shifrlash asosan qaysi xususiyatni himoyalaydi?|Ma’lumot maxfiyligini|Fayl nomi uzunligini|Elektr quvvatini|Monitor o‘lchamini
Ma’lumot yaxlitligi nimani anglatadi?|Ma’lumotning ruxsatsiz o‘zgartirilmaganligini|Faqat ma’lumotning katta hajmini|Har doim hammaga ochiqligini|Faqat arxiv nomini
Dasturlarni yangilash nima uchun muhim?|Ma’lum zaifliklarni tuzatish uchun|Faqat ikonka rangini almashtirish uchun|Parolni ommaga ochish uchun|Zaxirani o‘chirish uchun
Shubhali havola kelganda to‘g‘ri amal qaysi?|Manbani alohida ishonchli kanal orqali tekshirish|Darhol parolni kiritish|Havolani hammaga yuborish|Himoyani o‘chirish
''',
'Xalqaro munosabatlar': '''
Ko‘p tomonlama diplomatiya nimani anglatadi?|Bir nechta davlat ishtirokidagi muloqotni|Faqat ikki shaxs suhbati|Faqat ichki saylovni|Faqat mahalliy savdoni
Elchixona asosan qanday vazifani bajaradi?|Yuboruvchi davlatni qabul qiluvchi davlatda vakillik qilish|Faqat mahsulot ishlab chiqarish|Barcha mahalliy qonunlarni yozish|Barcha maktablarni boshqarish
Madaniyatlararo muloqotda qaysi yondashuv ma’qul?|Madaniy farqlarni hurmat qilib, aniqlashtiruvchi savol berish|Stereotiplarni mutlaq haqiqat deb olish|Suhbatdoshni kamsitish|Tarjimani doim rad etish
Milliy manfaat tushunchasi nimaga taalluqli?|Davlat va jamiyatning asosiy ehtiyoj va maqsadlariga|Faqat bitta korxona reklamasiga|Faqat shaxsiy kundalikka|Faqat bir sport o‘yiniga
''',
'Menejment': '''
Motivatsiya nima?|Faoliyatga undovchi omillar majmui|Faqat buyruq matni|Faqat ish stoli|Faqat jarima jadvali
Jamoaviy qaror afzalligi qaysi?|Turli tajriba va qarashlardan foydalanish|Mas’uliyatni doim yo‘qotish|Dalillarni chetga surish|Muammoni yashirish
Loyihada muddatni rejalashda nima hisobga olinadi?|Vazifalar davomiyligi va o‘zaro bog‘liqligi|Faqat loyiha nomi|Faqat xona rangi|Faqat xodimning bo‘yi
Manfaatlar to‘qnashuvi qachon yuzaga keladi?|Shaxsiy manfaat xizmat qaroriga ta’sir qilishi mumkin bo‘lganda|Har bir yig‘ilishda|Har qanday reja yozilganda|Har bir tanaffusda
''',
'Biznes va menejment': '''
Tadbirkorlik riski nimani anglatadi?|Kutilgan natijaga erishmaslik ehtimolini|Har qanday ishning kafolatli foydasini|Faqat hujjat sonini|Faqat mijoz yoshini
Biznes rejada bozor tahlili nima uchun kerak?|Talab, raqobat va mijozlarni tushunish uchun|Faqat sahifalar sonini oshirish uchun|Faqat rasm qo‘shish uchun|Faqat xodim suratlarini joylash uchun
Birlik narxi 50, o‘zgaruvchan xarajat 30 bo‘lsa, birlikning hissa marjasi qancha?|20|80|30|50
Mijozni saqlab qolish nimani anglatadi?|Mavjud mijoz bilan davomli aloqani rivojlantirish|Yangi mijozni butunlay taqiqlash|Mijozni majburlash|Reklamani yashirish
''',
'Moliya sohasida boshqaruv': '''
Investitsiya portfeli nima?|Investor egalik qiladigan investitsiyalar to‘plami|Faqat naqd pul hamyoni|Faqat korxona muhri|Faqat ish haqi ro‘yxati
Diskontlash nima?|Kelajakdagi pul oqimini bugungi qiymatga keltirish|Har doim narxni ikki baravar qilish|Faqat naqd pul sanash|Qarzni yashirish
Moliyaviy zaxira nima uchun tuziladi?|Kutilmagan xarajatlarni qoplash uchun|Barcha daromadni yashirish uchun|Hisobotni bekor qilish uchun|Doimiy zarar yaratish uchun
Qarz mablag‘larining ortishi odatda nimani kuchaytirishi mumkin?|Moliyaviy majburiyatlar va riskni|Foydaning mutlaq kafolatini|Har qanday xarajatning yo‘qolishini|Hisob yuritishga ehtiyoj yo‘qligini
''',
'Buxgalteriya hisobi va moliya': '''
Kreditorlik qarzi nima?|Korxonaning boshqalarga to‘lashi kerak bo‘lgan qarzi|Mijozning korxonaga qarzi|Faqat naqd tushum|Faqat ustav kapitali
Inventarizatsiya nimani tekshiradi?|Mavjud aktivlarni hisob ma’lumotlari bilan solishtiradi|Faqat xodimlar kayfiyatini|Faqat reklama matnini|Faqat bozor narxini
Boshlang‘ich hujjatning vazifasi nima?|Xo‘jalik operatsiyasini tasdiqlash|Faqat logotip ko‘rsatish|Faqat shaxsiy fikr yozish|Faqat binoni bezash
Hisoblash tamoyiliga ko‘ra daromad qachon tan olinadi?|Ishlab topilgan davrda, pul kelishidan qat’i nazar|Faqat naqd pul sanalganda|Faqat yil oxirida har qanday holatda|Faqat qarz olinganda
''',
'Xorijiy til va adabiyoti': '''
Choose the correct comparative form of “good”.|Better|Gooder|Bestest|More gooder
Which sentence is a question in the past simple?|Did you visit the museum?|Do you visited the museum?|Did you visited the museum?|Were you visit the museum?
The main character in a story is usually called what?|The protagonist|The publisher|The index|The footnote
What is the setting of a story?|The time and place of the events|Only the author’s name|Only the book price|Only the number of chapters
''',
'Maktabgacha ta’lim': '''
Yoshga mos topshiriq tanlashda nima muhim?|Bolaning rivojlanish darajasi va ehtiyojlari|Faqat kattalar uchun murakkabligi|Faqat jihoz narxi|Faqat daftar rangi
Birgalikdagi o‘yin qaysi ko‘nikmani rivojlantiradi?|Hamkorlik va navbat kutish|Faqat tez yozish|Faqat uzoq yodlash|Faqat jim turish
Kun tartibining izchilligi bolaga qanday yordam beradi?|Kutilayotgan faoliyatni anglab, o‘zini barqarorroq his qilishga|Har qanday mustaqillikni yo‘qotishga|Faqat ko‘proq vazifa berishga|O‘yinni butunlay bekor qilishga
Tarbiyachi bolaning yutug‘ini qanday qo‘llashi ma’qul?|Aniq harakat va urinishini e’tirof etish|Faqat boshqa bolalar bilan solishtirish|Yutuqni doim inkor qilish|Faqat sovg‘a talab qilish
''',
'Boshlang‘ich ta’lim': '''
Son tushunchasini rivojlantirishda qaysi faoliyat foydali?|Buyumlarni sanash va miqdorlarni solishtirish|Faqat raqamlarni izohsiz ko‘chirish|Faqat murakkab formulalarni yodlash|Sanashni taqiqlash
O‘quvchi savol bersa, o‘qituvchi qanday javob berishi ma’qul?|Savolni tinglab, tushunishga yordam berishi|Uni doim to‘xtatishi|Savolni masxara qilishi|Barcha savolni jazolashi
Hamkorlikdagi o‘qish uchun nima zarur?|Aniq umumiy vazifa va ishtirok imkoniyati|Faqat bitta o‘quvchining ishlashi|Vazifani tushuntirmaslik|O‘zaro gaplashishni doim taqiqlash
O‘qish ravonligi nimani o‘z ichiga oladi?|Matnni aniq, mos tezlik va ifoda bilan o‘qish|Faqat juda tez o‘qish|Faqat ovozni baland qilish|Matnni tushunmay yodlash
''',
'Pedagogika': '''
Ta’limda teskari aloqa qachon foydaliroq?|O‘z vaqtida va aniq bo‘lganda|Faqat yil tugagach aytilganda|Faqat umumiy tanqid bo‘lganda|Faqat shaxsga qaratilganda
Muammoli ta’lim nimaga asoslanadi?|Muammoni izlash va yechish orqali o‘rganishga|Faqat javobni oldindan ko‘chirishga|Har savolni bekor qilishga|Faqat buyruq yodlashga
Ta’lim metodini tanlashda nima hisobga olinadi?|Maqsad, mazmun va o‘quvchi ehtiyojlari|Faqat o‘qituvchi kiyimi|Faqat xona raqami|Faqat qo‘ng‘iroq ovozi
Mustaqil o‘rganish ko‘nikmasi qaysi amal bilan rivojlanadi?|Maqsad qo‘yish va o‘z natijasini tekshirish|Barcha topshiriqni boshqaga bajartirish|Manbani tekshirmasdan ko‘chirish|Savollardan qochish
''',
'Psixologiya': '''
Faol tinglashga qaysi misol mos?|Suhbatdosh fikrini aniqlashtirib qayta ifodalash|Gapni doim bo‘lish|Darhol ayblash|Faqat o‘z hikoyasini aytish
Xotiraning vazifasi nima?|Axborotni eslab qolish, saqlash va qayta tiklash|Faqat tovush chiqarish|Faqat ko‘rish|Faqat tana harakati
Nazorat guruhi tadqiqotda nima uchun kerak?|Ta’sir natijasini solishtirish uchun|Barcha javobni belgilash uchun|Ishtirokchilarni majburlash uchun|Dalillarni yashirish uchun
Stereotip nima?|Guruh haqida umumlashtirilgan, soddalashtirilgan tasavvur|Har bir insonning aniq o‘lchovi|Faqat ilmiy isbotlangan qonun|Faqat shaxsiy xotira
''',
'Filologiya va tillarni o‘qitish (Ingliz tili)': '''
Choose the correct conditional sentence.|If it rains, we will stay home.|If it rain, we stays home.|If it rains, we will stayed home.|If it raining, we stay yesterday.
Which word contains a prefix?|Unhappy|Happiness|Teacher|Quickly
Morfologiya nimani o‘rganadi?|So‘z shakllari va tuzilishini|Faqat nutq tovushlarini|Faqat yozuv qog‘ozini|Faqat kitob narxini
When teaching new vocabulary, which approach provides useful context?|Using the words in meaningful sentences|Listing words without examples only|Avoiding all usage|Teaching spelling without meaning only
'''
}


def seed_questions(name):
    source = SUBJECTS.get(name)
    if source is None:
        return []
    questions = []
    for index, line in enumerate((source + SUBJECTS[RELATED[name]] + EXTRA[name] + COMMON).strip().splitlines()):
        if not line.strip():
            continue
        text, *options = line.split('|')
        offset = len(questions) % 4
        options = options[-offset:] + options[:-offset] if offset else options
        questions.append({'text':text,'options':options,'correct':offset})
    return questions
