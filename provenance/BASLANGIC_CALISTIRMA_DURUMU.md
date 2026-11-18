# Gerçek Çalıştırma Durumu

Tarih: 18 Kasım 2026. Bu belge yalnızca gerçekten yapılan işlemleri kaydeder.

## Tamamlananlar

- Kaynak veri sürümleri sabitlendi ve indirildi.
- Her dilde 15.000 metinlik dengeli alt küme hazırlandı: 11.400 eğitim, 600 doğrulama, 3.000 test.
- Testte her gerçek sınıftan 1.000 yorum vardır; tüm yöntemler aynı test dosyalarını kullanmalıdır.
- Beş yazılım testi geçti: ID eşleştirme, hatalı çıktı denetimi, tekrar/çelişki temizliği, sızıntısız örnekleme ve VADER eşik sınırları.
- Orijinal VADER ile İngilizce test ve Türkçe doğrudan tanısal test tamamlandı.

## Kaynak denetimi

| Dil | Kaynak negatif/nötr/pozitif | Temiz negatif/nötr/pozitif | Tekrar nedeniyle çıkarılan satır | Çelişkili etiket grubundaki çıkarılan satır |
|---|---|---|---:|---:|
| EN | 11377/27479/21043 | 11374/27458/21033 | 26 | 8 |
| TR | 50000/50000/50000 | 46412/45354/48227 | 3082 | 6925 |

Çelişkili etiketli tekrarların tamamı çıkarılmıştır. Bunlar satır sayılarıdır, benzersiz metin sayısı değildir. Bu denetim yakın tekrar veya tüm yanlış etiketleri belirlediği anlamına gelmez.

## İlk sonuçlar

| Dil / Yöntem | Negatif yanlış / 1.000 | Nötr yanlış / 1.000 | Pozitif yanlış / 1.000 | Toplam yanlış / 3.000 | Accuracy | Macro-F1 |
|---|---:|---:|---:|---:|---:|---:|
| EN / orijinal VADER | 447 | 579 | 292 | 1318 | %56.07 | 0.5564 |
| TR / doğrudan VADER — tanısal | 976 | 44 | 877 | 1897 | %36.77 | 0.2534 |

Her sınıfın yanlış sayısı gerçek etiketi o sınıf olan yorumlarda sayılmıştır. Tablodaki sonuçlar yalnızca burada dondurulan dengeli alt kümeye aittir.

Türkçede orijinal VADER 3.000 yorumun 2.772’sini nötr tahmin etmiştir. Yüksek nötr recall değeri diğer sınıfların nötre yığılmasıyla birlikte yorumlanmalıdır. Bu sonuç Türkçeye uyarlanmış bir VADER sisteminin başarımı olarak sunulmamalıdır. Alan ve etiketleme farkları nedeniyle dil farkı hakkında tek başına nedensel sonuç vermez.

## Henüz yapılmayanlar

- Türkçe çeviri + VADER hattı veya hocanın uygun gördüğü VADER uyarlaması.
- İngilizce BERT ve Türkçe BERTurk fine-tuning.
- LLM seçimi, pilot ve tam test çalıştırması.
- Üç yöntemin ortak sonuç grafikleri ve akademik hata incelemesi.
- Sonuçlarla doldurulmuş Word raporu.
- Grubun üç üyesinin konuştuğu sunum videosu.
- E-posta, OneDrive veya elden teslim.

## Bir sonraki adım

Çalışma ortamı ve LLM erişimi seçildikten sonra BERT ve LLM çalıştırıcıları hazırlanacak. Prompt ve hiperparametre seçimi validation üzerinde yapılmalı; bu ilk test sonuçlarına göre test için optimizasyon yapılmamalıdır.

## Kaynak sürümleri

- EN: `cardiffnlp/tweet_eval` — `b3a375baf0f409c77e6bc7aa35102b7b3534f8be`
- TR: `maydogan/Turkish_SentimentAnalysis_TRSAv1` — `3bda52ed2c57ac1e80ac463192cafeeae9f72213`
