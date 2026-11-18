# Ödev yönergesine uygunluk kontrolü

Kontrol tarihi: 18 Kasım 2026. Dayanak, öğrencinin paylaştığı öğretim elemanı yönergesidir. Son teslim **25 Kasım 2026 Çarşamba ders saatidir**. Bu belge not veya kabul garantisi vermez; tamamlanan işi ve kalan gereksinimleri ayırır.

## Sonuç

Projenin veri, deney, değerlendirme ve rapor altyapısı yönergenin teknik çekirdeğini karşılıyor. Altı temel koşum ve 18.000 test tahmini gerçek sonuçlardan doğrulandı. Üç üyenin kapak, ders ve öğretim elemanı bilgileri tamamlandı. Proje teslim için henüz tamamlanmış sayılmaz: en fazla 10 dakikalık gerçek video ve iki zorunlu teslim kanalı bekliyor. Türkçe VADER uygulamasının yöntemsel kapsamı ayrıca güçlendirilmelidir.

## Gereksinim ve kanıt eşleştirmesi

| Yönerge | Mevcut durum | Kanıt veya kalan iş |
|---|---|---|
| İngilizce etiketli pozitif negatif nötr veri; sınıf başına en az 1.000 | Karşılanıyor | TweetEval sentiment. Seçili havuzda sınıf başına 5.000; testte sınıf başına 1.000 |
| Türkçe etiketli pozitif negatif nötr veri; sınıf başına en az 1.000 | Karşılanıyor | TRSAv1. Seçili havuzda sınıf başına 5.000; testte sınıf başına 1.000 |
| İki dilde VADER | Çalıştırıldı; Türkçe yöntemsel çekince var | EN orijinal VADER. TR orijinal İngilizce sözlükle doğrudan tanısal deney; uyarlanmış Türkçe sistem değildir |
| İki dilde BERT tabanlı duygu analizi | Karşılanıyor | İngilizce BERT ve BERTurk üç sınıflı başlıkla eğitim bölümünde fine tuning gördü |
| İki dilde LLM tabanlı duygu analizi | Karşılanıyor | Aynı Qwen2.5 7B instruction modeli; zero-shot prompt, validation pilotu ve tam testler |
| Her yöntem dil ve gerçek sınıf için yanlış sayıları | Karşılanıyor | 6 koşum × 3 sınıf = 18 hata sayısı; comparison.csv ve class_metrics.csv |
| Kaynakları yöntemleri parametreleri ve karşılaştırmaları içeren Word | Kapak ve mimari ayrıntıları tamamlandı | Yerel teslim raporu tam öğrenci bilgilerini içerir. GitHub raporunda öğrenci numaraları gizlidir |
| Çalıştırılabilir temiz kodlar | Mevcut koşullarda doğrulandı | .py dosyaları, sabit sürümler, README komutları, 14 yazılım testi ve veri denetimleri |
| Akademik hata yorumu | Temel inceleme hazır; derinleştirme önerilir | Beş açıklamalı vaka, 90 örneklik inceleme CSV'si. Bağımsız insan incelemesi yapılmış sayılmaz |
| Tam üç kişilik grup | Belgelenmiştir | Tuba Deligöz, Özge Çelik ve Tuba Rukiye Dan. Konuşma taslağında üç üye için önerilen akış var; video henüz kaydedilmedi |
| Herkesin aktif olduğu en fazla 10 dakika video | Eksik | Dokuz dakikalık konuşma taslağı hazır; bu bir video kaydı değildir |
| Derste imza karşılığında elden teslim | Yapılmadı | 25 Kasım ders saatinde grup gerçekleştirecek |
| E-posta ile teslim | Yapılmadı | Word, kod ve video gönderilecek; alıcı bilgisi doğrulanacak |
| Eklenti sınırında OneDrive bağlantısı | Koşula bağlı; gerekirse yapılacak | Üç materyal türü de aynı OneDrive klasöründe bulunacak; alıcının erişimi kontrol edilecek |

## Sınıf bazlı gerçek hata sayıları

Her hücrenin paydası 1.000 test yorumudur. Aynı dilde bütün yöntemler aynı test ID'leri üzerinde değerlendirildi. Geçersiz çıktı sayısı sıfırdır.

| Dil | Yöntem | Negatif yanlış | Nötr yanlış | Pozitif yanlış |
|---|---|---:|---:|---:|
| EN | VADER | 447 | 579 | 292 |
| EN | BERT | 148 | 497 | 285 |
| EN | Qwen | 250 | 278 | 423 |
| TR | VADER doğrudan tanısal | 976 | 44 | 877 |
| TR | BERT | 150 | 240 | 141 |
| TR | Qwen | 106 | 569 | 115 |

Yönergede hedef accuracy şartı yoktur. Düşük model başarımı tek başına ödeve aykırılık değildir; yöntemin doğru uygulanması ve sonucun doğru yorumlanması gerekir.

## Teknik açıdan dikkat gerektiren noktalar

**Türkçe VADER.** Mevcut koşum, standart sözlüğün Türkçe karşısındaki davranışını ölçer; anlamlı bir Türkçe uyarlama deneyinin yerine geçtiği iddia edilmemelidir. Yönerge çeviri yöntemini zorunlu tutmuyor. Ancak aynı 3.000 test ID'sinde Türkçe → İngilizce çeviri + VADER ek deneyi, üç yöntemin Türkçe karşılaştırmasını güçlendirecek en önemli teknik adımdır. Kod hazır, gerçek çeviri koşumu henüz yapılmadı. Doğrudan deney korunmalı; çeviri sonucu ayrı ad ve sınırlılıklarla raporlanmalı. VADER'ın özgün deposunda İngilizce dışındaki metinleri çeviriyle ele alan örnekler vardır: [özgün VADER deposu](https://github.com/cjhutto/vaderSentiment).

**Veri alanı.** İngilizce kaynak sosyal medya, Türkçe kaynak ürün yorumudur. Yönerge ürün yorumuna özel bir alan kısıtı koymuyor. Alan ve etiketleme farkı, diller arası sonuçların sınırlılığı olarak korunmalıdır.

**LLM seçimi.** Yönergedeki GPT, Llama ve Claude adları örnektir. Qwen, instruction-tuned büyük dil modeli olduğu için kullanılan prompting yaklaşımı LLM kategorisindedir. Ücretli API veya belirli bir marka zorunlu yazılmamıştır. [Qwen model kartı](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct).

**Rapor ayrıntısı.** Model kimlikleri, sınıflandırma başlığı ve eğitim/üretim ayarlarına ek olarak mimari açıklama güçlendirildi: 12 encoder katmanı, 12 dikkat başlığı, 768 gizli boyut; sözlük EN 30.522, TR 32.000 token. Bu bilgiler best/config.json kayıtlarından alındı. Qwen'in decoder mimarisi, 28 katmanı, GQA başlıkları ve Q4_K_M nicemleme koşulları model kartıyla birlikte eklendi. Doğrulama pilotlarının gerçek metrikleri ayrı tabloda gösterildi.

**Tekrar üretilebilirlik.** Türkçe LLM'de iki Ollama sürümü kullanılması ve bazı uçtan uca sürelerin kaydedilememesi raporda açıklandı. Bunlar sonuçların uydurma olduğu anlamına gelmez; deney sınırlılıklarıdır. Ana modelleri test sonucuna göre yeniden seçmekten kaçınılmalıdır.

## Kalan aşamalar için önerilen sıra

1. Türkçe VADER'ın uyarlama kapsamını netleştirin; çeviri + VADER ek koşumunu tamamlayın veya tanısal kullanımın gerekçesini öğretim elemanıyla teyit edin.
2. Kapak ve mimari ayrıntıları tamamlandı. Üyeler kendi yöntemlerini ve hata örneklerini inceleyerek gerçek katkılarını kaydetsin.
3. Konuşma taslağını üç kişi prova edin. Videoyu herkes aktif konuşacak şekilde kaydedin; süreyi gerçekten ölçün.
4. Güncel rapor, kodlar ve videonun bütünlüğünü ve açılabildiğini kontrol edin.
5. 25 Kasım ders saatinde imza karşılığı elden ve e-posta ile teslim edin. Boyut sınırına takılırsanız OneDrive erişim bağlantısını e-postaya ekleyin.

GitHub paylaşımı bu beşinci adımın yerine geçmez. E-posta veya teslimin yapıldığı, yalnızca GitHub'a yükleme üzerinden işaretlenmemelidir.
