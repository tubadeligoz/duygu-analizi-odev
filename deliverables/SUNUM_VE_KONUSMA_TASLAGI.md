# Üç kişilik sunum akışı ve konuşma taslağı

Hedef süre **9 dakika**, üst sınır **10 dakika**. Tam üç konuşmacı; her biri yaklaşık üç dakika. Bu dosya konuşma taslağıdır; video kaydı değildir. Konuşmacı adları aşağıdaki önerilen akışa yerleştirildi; bu bir video kaydı değildir. Prova süresine göre örnek sayısını azaltın; sayıları veya sınırlılıkları değiştirmeyin.

| Zaman | Konuşmacı | Gösterilecek içerik |
|---|---|---|
| 00:00–01:00 | Tuba Deligöz | Amaç ve veri kaynakları |
| 01:00–02:00 | Tuba Deligöz | Dengeli bölümler ve sızıntı kontrolü |
| 02:00–03:00 | Tuba Deligöz | Deney tasarımı ve metrikler |
| 03:00–04:00 | Özge Çelik | VADER ve Türkçe tanısal kullanım |
| 04:00–05:00 | Özge Çelik | BERT eğitimi ve checkpoint seçimi |
| 05:00–06:00 | Özge Çelik | Karşılaştırma tablosu ve sınıf hataları |
| 06:00–07:00 | Tuba Rukiye Dan | LLM pilotu ve test koşulları |
| 07:00–08:00 | Tuba Rukiye Dan | Gerçek hata örnekleri |
| 08:00–09:00 | Tuba Rukiye Dan | Sınırlılıklar ve kapanış |

## Tuba Deligöz için konuşma taslağı 00:00–03:00

Bu çalışmada İngilizce ve Türkçe metinlerde negatif, nötr ve pozitif duygu sınıflandırmasını üç yöntemle karşılaştırdık. VADER bir sözlük ve kural sistemi, BERT etiketli veriyle eğitilen bir dil modeli, Qwen ise temel deneyde örnek gösterilmeden kullanılan büyük dil modelidir. Amacımız yalnızca tek bir başarı yüzdesi bulmak değildi. Hangi gerçek sınıfın başka hangi sınıfa karıştığını da ölçtük.

İngilizce kaynak CardiffNLP TweetEval’in sentiment bölümüdür ve sosyal medya metinleri içerir. Türkçe kaynak TRSAv1 ürün yorumlarıdır. Kaynak sınıflarının her biri en az bin yorum koşulunu karşılar. Türkçe kaynağın ilk hali her sınıfta elli bin yorum içerir. İngilizce kaynak sayıları, veri sürümleri ve hashler manifestte kayıtlıdır. Bu iki alan farklı olduğu için sonuçlar arasındaki farkı yalnızca dile bağlayamayız.

Her dilde eğitimde on bir bin dört yüz, doğrulamada altı yüz, testte üç bin metin kullandık. Sınıf başına bunlar üç bin sekiz yüz, iki yüz ve bin örnektir. Bölümler daha önce hazırlanmıştı; yeniden örnekleme yapmadık. Boş metni, tam tekrarları, çelişkili etiketleri ve bölümler arasında aynı metnin geçmesini denetledik. Otuz bin satırın ve altı dosyanın bütünlüğü doğrulandı. Emoji, büyük harf, noktalama ve olumsuzluk sözcükleri korundu.

BERT yalnızca eğitim etiketleriyle öğrendi. Doğrulama verisi checkpoint seçimi için kullanıldı. LLM pilotu da doğrulama verisinde yapıldı. Testten prompt veya hiperparametre seçmedik. Aynı dilde üç yöntem tam olarak aynı test ID’lerine tahmin verdi; satır sırası üzerinden eşleştirme yapmadık. Test etiketlerini modele göndermedik.

Accuracy doğru sayısının toplam örneğe oranıdır. Macro F1 ise üç sınıfın F1 değerlerinin ortalamasıdır. Sınıfın yanlış sayısını, gerçek etiketi o sınıf olan bin örnekten doğru bulunanları çıkararak hesapladık. Geçersiz cevap olsaydı paydadan çıkarmayacaktık. Şimdi arkadaşım VADER ve BERT sonuçlarını anlatacak.

## Özge Çelik için konuşma taslağı 03:00–06:00

VADER’da orijinal vaderSentiment üç nokta üç nokta iki sürümünü ve standart compound eşiklerini kullandık. Eksi sıfır virgül sıfır beş ve altı negatif, artı sıfır virgül sıfır beş ve üstü pozitif, arası nötrdür. İngilizce testte accuracy yüzde 56,07, Macro F1 0,5564 çıktı. Gerçek negatif sınıfta 447, nötr sınıfta 579, pozitif sınıfta 292 hata var.

VADER’ın standart sözlüğü İngilizcedir. Bu nedenle Türkçeye doğrudan uygulamayı tanısal başlangıç deneyi olarak adlandırdık. Türkçe destekli bir sistemmiş gibi sunmuyoruz. Üç bin Türkçe yorumun iki bin yedi yüz yetmiş ikisini nötr tahmin etti. Accuracy yüzde 36,77 ve Macro F1 0,2534. Yüksek nötr recall, diğer sınıfların nötre yığılmasını gizlememeli. Çeviri ve VADER için ayrı bir çalıştırıcı hazırladık; bu ek deney yapılmadığı için sonuç yazmadık.

BERT tarafında İngilizcede bert base uncased, Türkçede BERTurk cased başlangıç modellerini kullandık. Üç sınıflı başlık ekleyip bütün parametreleri eğitim verisinde güncelledik. Öğrenme oranı iki çarpı on üzeri eksi beş, batch on altı, uzunluk iki yüz elli altı token, en fazla üç epoch ve seed kırk ikidir. Modellerin commitleri ve tokenizer sürümleri kaydedildi.

İki dilde de en iyi checkpoint üçüncü epoch oldu; karar yalnızca validation Macro F1 ile verildi. Teste göre yeniden eğitim ayarı seçmedik. RTX 3080 Ti üzerinde İngilizce optimizasyon yaklaşık 116,5, Türkçe 119,6 saniye sürdü; bu süreler indirme ve checkpoint yazmayı kapsamıyor.

İngilizce BERT accuracy yüzde 69, Macro F1 0,6843 verdi. Negatif yanlış sayısı 148’e indi; nötrde 497 hata kaldı. Türkçe BERT accuracy yüzde 82,30, Macro F1 0,8234 verdi; sınıf hataları negatifte 150, nötrde 240 ve pozitifte 141 oldu. Karışıklık matrisleri hangi sınıfın nereye gittiğini gösteriyor. İngilizcede Qwen’in Macro F1 değeri BERT’ten çok az yüksek, accuracy değeri ise biraz düşük. Bu küçük fark için anlamlılık testi yapmadık. Arkadaşım LLM koşumunu ve hata örneklerini açıklayacak.

## Tuba Rukiye Dan için konuşma taslağı 06:00–09:00

İki dilde aynı yerel Qwen2.5 yedi milyarlık instruction modelini kullandık. Model test sonuçları görülmeden, bilgisayarda bulunduğu ve on iki gigabayt GPU’ya sığdığı için seçildi. Ağırlık digest’i iki dilde aynıdır. Prompt ve sınıf tanımları da aynıdır. Her dilde validation’dan sınıf başına on, toplam otuz yorumla pilot yaptık; promptu değiştirmeden tam teste geçtik.

Modelden sadece negative, neutral veya positive kabul ettik. Her yorumun ID’sini, ham yanıtını, gecikmesini, bütün denemeleri ve token kullanımını kaydettik. Timeout ve tekrar deneme desteği ekledik. Hatalı cevapları nötre çevirmiyoruz; ayrı geçersiz çıktı olarak tutuyoruz. Tam testlerde geçersiz çıktı çıkmadı. Ücretli API çağrısı yapılmadı; yerel model kullanıldı.

İngilizce Qwen accuracy yüzde 68,30 ve Macro F1 0,6867 verdi. Türkçe accuracy yüzde 73,67 ve Macro F1 0,7187. Türkçe negatifte yalnızca 106, pozitifte 115 hata varken nötrde 569 hata var. Bu nedenle tek bir ortalama puan sınıf davranışını yeterince açıklamıyor.

Örneğin “kokusu çok güzel ama saçımda bir etkisini görmedim” yorumunun kaynak etiketi pozitif, BERT ve Qwen tahmini nötrdür. Aynı metin hem beğeni hem olumsuz deneyim içerir. “Abarttıkları kadar olmasada idare eder bir ürün” kaynakta negatifken Qwen nötr demiştir. Bunlar nötr sınıf sınırını tartışmaya açar. “Aşırı iyi ürün herkese almasını tavsiye ederim” metninin kaynakta negatif olması olası etiket gürültüsüdür; bağımsız inceleme olmadan kesin hata demiyoruz. Altın etiketleri değiştirmedik. İroni ve olumsuzluk örnekleri de raporda var.

Sınırlılıklarımız şunlar: iki dilin alanları farklı, BERT denetimli ama Qwen zero shot, ana eğitim tek seed içeriyor ve açık verinin ön eğitimde görülmediği garanti edilemiyor. Türkçe LLM koşumu servis güncellemesiyle kesildi; ilk 2318 tahmin korundu, kalan 682 aynı ağırlık ve promptla tamamlandı. Ollama 0.40.15 ve 0.40.16 farkını raporladık.

Bu sabit testte Türkçe BERT en yüksek genel Macro F1’i verdi. İngilizcede accuracy ve Macro F1 sıralaması farklılaşabiliyor. Kullanım kararı verirken gerçek sınıf hatalarını, eğitim koşullarını ve süreleri birlikte değerlendirmek gerekiyor. Kodlar, sabit veriler, gerçek sonuçlar ve çalıştırma komutları teslim paketinde bulunuyor.

## Prova ve kayıt notları

Metni doğal konuşma hızınızla prova edin. Konuşmacı geçişleri dahil süreyi ölçün; toplam 10 dakikayı aşarsa yöntem açıklamalarını kısaltın. Grafiklerde sınıf ve yöntem adlarını okunur büyüklükte gösterin. Üç kişi de aktif konuşmalı. Dosya, video kaydı veya gerçek teslim yapılmış olduğunu göstermez.
