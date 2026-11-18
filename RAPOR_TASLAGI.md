# Karşılaştırmalı Duygu Analizi: İngilizce ve Türkçe Metinlerde VADER, BERT ve LLM

**Durum: İçerik iskeleti. Henüz tamamlanmış Word raporu veya sonuç raporu değildir.**

## Kapak

Ders, öğretim elemanı, tam 3 grup üyesinin adı ve öğrenci numarası, teslim tarihi.

## Özet

Gerçek deneyler bittikten sonra: amaç, kaynaklar, örneklem, yöntemler, temel sayısal
bulgu ve en önemli sınırlılık. Sonuç beklenirken başarı yüzdesi yazılmayacak.

## 1. Giriş

Duygu analizi problemi; kural tabanlı, denetimli temsil öğrenme ve LLM yaklaşımlarının
karşılaştırılma gerekçesi. Araştırma sorusu ve testten önce belirlenen hipotezler.

## 2. Veri Setleri

Kaynak ve akademik referans; dil, alan, etiket tanımı, kaynak sınıf sayıları,
temizlik sonrası sayılar, çıkarılan tekrar/çelişki sayıları. Etiketleme yöntemi
belgelenebildiği ölçüde açıklanmalı; bilinmeyen kısım varsayılmamalı.
Train/validation/test sayıları ve örnekleme seed'i. Veri sürümü/commit'i.

## 3. Yöntemler

### 3.1 VADER

Sözlük ve kurallar, compound eşikleri, Türkçe doğrudan kullanımın sınırlılığı,
varsa çeviri modelinin kimliği ve çeviri destekli hattın tanımı.

### 3.2 BERT

Model kimliği ve commit'i, tokenizer, üç sınıflı başlık, eğitim parametreleri,
epoch/checkpoint seçimi, kayıp fonksiyonu, donanım, süre ve kesilen metin oranı.

### 3.3 LLM

Model ve sürüm, API veya yerel koşum, tam prompt, zero/few-shot durumu,
üretim parametreleri, çıktı doğrulama, tekrar deneme politikası, başarısız yanıt sayısı.

## 4. Deney Tasarımı ve Metrikler

Aynı dilde aynı test ID'leri, veri sızıntısını önleme, validation/test ayrımı,
Accuracy, Macro-F1, precision/recall/F1 ve sınıf bazlı yanlış sayısı tanımı.
Başarısız model yanıtlarının toplam paydaya dahil edilmesi.

## 5. Sonuçlar

Her iki dilin üç yöntemi için toplam 6 temel satır. Türkçe VADER ek deneyi varsa
ayrı ve adı açık bir satır. Gerçek sınıf başına n, doğru, yanlış, hata oranı.
Karışıklık matrisleri; yöntem süreleri, bellek veya API kullanımı/maliyeti.
Eksik deneyler tabloda tamamlanmış gibi gösterilmeyecek.

## 6. Hata Analizi

Sistematik seçilmiş yanlış örneklerde olumsuzluk, ironi, karışık duygu, nötr sınırı,
emoji, yazım ve etiket gürültüsü. Her örnekte ID, gerçek etiket, tahmin ve açıklama.
Başarısızlık nedeni yorumunun gözlemden farklı olduğu açıkça anlaşılmalı.

## 7. Tartışma ve Sınırlılıklar

Dil ile alan farkının birbirine karışması; BERT denetimli/LLM zero-shot koşulları;
VADER'ın Türkçe uyarlaması ve çeviri hatası; açık veride ön eğitim kontaminasyonu;
etiket kalitesi; tek seed ve örnekleme boyutu; hesaplama ve süre kısıtları.

## 8. Sonuç

Yalnızca ölçümlerle desteklenen çıkarımlar ve hangi kullanım için hangi koşullarda
bir yöntemin tercih edilebileceği. Ölçülmeyen genellemelerden kaçınılmalı.

## Kaynakça ve Ekler

Veri setlerinin özgün makaleleri, VADER, BERT, BERTurk ve seçilen LLM'nin temel
kaynakları; model/dataset URL'leri ve erişim tarihleri. Tam prompt, ortam sürümleri,
parametreler, çalıştırma komutları ve üç üyenin katkı beyanı.
