# Gerçek çalıştırma durumu

Tarih 18 Kasım 2026. Yalnızca gerçek ölçümler yazılmıştır.

## Akademik rapor güncellemesi

22 Kasım 2026 tarihinde mevcut deneyler korunarak tez düzeninde genişletilmiş Word raporu hazırlandı. Rapor 8 bölüm, 33 atıf yapılan kaynak, 9 sayısal tablo, 7 grafik ve 6 denklem içerir. Türkçe özet, İngilizce abstract, literatür, yöntem, bulgular, hata çözümlemesi, geçerlilik tartışması ve ekler eklendi. Akademik rapor `deliverables/Proje_Raporu_Tez.docx` içindedir; öğrenci numaralarını içeren yerel teslim kopyası `teslim_ozel/Proje_Raporu_Tez.docx` altında tutulur. Kısa rapor ve bütün deney çıktıları korunmuştur. Bu güncellemede yeni model eğitimi veya çıkarımı yapılmadı.

## Tamamlananlar

- Özgün arşivin 31 dosyayla eşleşmesi ve yedeği.
- Her dilde 15.000 sabit metin; altı bölümün hash ve sızıntı denetimi.
- Önceki beş Python dosyası, manifest, veriler ve VADER çıktıları korunarak metriklerin doğrulanması.
- İki BERT modelinin seed 42 ile üç epoch fine tuning eğitimi; validation Macro F1 ile seçilen checkpointler.
- Her dilde 30 validation yorumuyla LLM pilotu; aynı Qwen ağırlıkları ve promptla iki tam test.
- Altı koşumda 18.000 ID eşleşmiş test tahmini; geçersiz çıktı sıfır.
- 14 anlamlı yazılım testi; veri, kayıt, model ve prompt kimliği denetimleri.
- Sınıf metrikleri, hata yönleri, karışıklık matrisleri, yanlış yorum CSV'leri ve gerçek grafikler.
- Türkçe Word raporu, beş açıklamalı gerçek hata vakası ve 90 örneklik insan inceleme listesi.
- Üç kişi için toplam 9 dakikalık sunum akışı ve konuşma taslağı.

## Gerçek test sonuçları

| Dil | Yöntem | Negatif yanlış | Nötr yanlış | Pozitif yanlış | Accuracy | Macro F1 |
|---|---|---:|---:|---:|---:|---:|
| EN | VADER | 447 | 579 | 292 | %56.07 | 0.5564 |
| EN | BERT | 148 | 497 | 285 | %69.00 | 0.6843 |
| EN | Qwen 2.5 7B | 250 | 278 | 423 | %68.30 | 0.6867 |
| TR | VADER tanısal | 976 | 44 | 877 | %36.77 | 0.2534 |
| TR | BERT | 150 | 240 | 141 | %82.30 | 0.8234 |
| TR | Qwen 2.5 7B | 106 | 569 | 115 | %73.67 | 0.7187 |

## Koşullar ve kesinti

BERT: RTX 3080 Ti 12 GB; batch 16, LR 2e-5, max length 256, 3 epoch, seed 42, FP16. Her iki dilde seçilen epoch 3. EN validation Macro F1 0.7469; TR 0.8511. EN optimizasyon 116.54 s ve test çıkarımı 2.46 s; TR 119.63 s ve 2.74 s. Bu optimizasyon süresi indirme, kodlama ve checkpoint yazmayı kapsamaz.

LLM: Qwen2.5 7B Instruct Q4_K_M; prompt hash 06cbb38c59dab736259c3a15e4c1daa100aadf38e40c7c0a5615843ba4236091. Bu hash yapılandırma ile promptun ortak deney hashidir. Aynı model digest iki dilde korundu. EN pilot Macro F1 0.5477; TR pilot 0.7629. Prompt değiştirilmedi. EN test Ollama 0.40.15; TR ilk 2.318 kayıt 0.40.15 ve kalan 682 kayıt 0.40.16 ile, kayıtlar korunarak tamamlandı. Güncelleme yalnızca çalıştırıcıya aittir; ağırlık digest, chat template ve prompt değişmedi. Sürüm farkı sınırlılık olarak raporlandı. Yerel çalışma için sağlayıcı API ücreti yok; enerji maliyeti ölçülmedi.

İngilizce test LLM duvar süresi 89.56 s; istek gecikmeleri toplamı 178.91 s. Türkçe son oturum 41.79 s; bütün yorumların gecikme toplamı 507.23 s. İki paralel istek nedeniyle toplam gecikme duvar süresine eşit değildir. Türkçe ilk oturumun tam duvar süresi kesintide kaydedilemedi.

## Çalıştırılmayan ve insana ait işler

- İsteğe bağlı Türkçe çeviri ve VADER hattı: kod hazır, deney yapılmadı.
- Üç seed BERT tekrarı: komutlar hazır, çalıştırılmadı.
- Ücretli API: yapılandırılabilir çalıştırıcı ve maliyet onay kapısı var; gerçek API çağrısı yapılmadı.
- İki grup üyesinin bağımsız hata kodlaması yapılmadı.
- Üç grup üyesinin adı, öğrenci numaraları, ders ve öğretim elemanı bilgileri yerel teslim raporunda tamamlandı. GitHub kopyasında öğrenci numaraları gizlidir.
- Konuşma taslağı video değildir; video kaydı yapılmadı.
- E posta, bulut paylaşımı, elden teslim veya gerçek gönderim yapılmadı.

## Kanıt dosyaları

`audit/data_integrity.json`, `provenance/archive_verification.json`, `audit/delivery_validation.json`, `audit/model_artifacts.json`, `data/manifest.json`, `runs/*/config.json`, `runs/*/history.json`, `runs/*/evaluation/metrics.json`, `runs/*llm*/records.jsonl` ve `deliverables/comparison.csv`. Word sayfalarının görsel denetimi `audit/document_visual_qa.json` kaydında belirtilir.
