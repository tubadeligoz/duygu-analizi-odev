"""Write current Turkish run instructions and a three-person nine-minute script."""
import json
from pathlib import Path

from common import read_csv, write_csv, write_json
from experiment_utils import ROOT, utc_now


def main():
    group_path = ROOT / "configs/group_members.public.json"
    group = json.loads(group_path.read_text(encoding="utf-8")) if group_path.exists() else None
    rows = read_csv(ROOT / "deliverables/comparison.csv")
    table = "| Dil | Yöntem | Negatif yanlış | Nötr yanlış | Pozitif yanlış | Accuracy | Macro F1 |\n|---|---|---:|---:|---:|---:|---:|\n"
    for r in rows:
        table += f"| {r['language'].upper()} | {r['method']} | {r['negative_incorrect']} | {r['neutral_incorrect']} | {r['positive_incorrect']} | %{float(r['accuracy'])*100:.2f} | {float(r['macro_f1']):.4f} |\n"
    readme = r'''# İngilizce ve Türkçe karşılaştırmalı duygu analizi

Teslim tarihi **25 Kasım 2026**. Grup tam **3 kişi**. Güncel durum: altı temel deney tamamlandı; Word raporu, gerçek sonuç tabloları, grafikler ve üç kişilik konuşma taslağı hazırlandı. Grup bilgileri, insan incelemesi, video ve gerçek teslim tamamlanmış sayılmamıştır.

## Başlamak için

- `deliverables/Proje_Raporu.docx`: Türkçe rapor.
- `deliverables/comparison.csv`: gerçek altı satırlık karşılaştırma.
- `deliverables/SUNUM_VE_KONUSMA_TASLAGI.md`: tam üç kişi için 9 dakika.
- `deliverables/TESLIM_KONTROL_LISTESI.md`: tamamlanan ve insan katkısı bekleyen işler.
- `CALISTIRMA_DURUMU.md`: gerçek koşumlar ve sınırlılıklar.

Arşiv, masaüstündeki `Duygu_Analizi_Odev.zip` adıyla bulundu. 31 dosyanın mevcut klasörle birebir eşleştiği doğrulandı; eksik dosya yoktu. Veri, mevcut kod ve VADER çıktıları yeniden üretilmedi veya değiştirilmedi. Özgün ZIP ve önceki README/durum belgeleri `provenance/` altında korundu. İlk adı belirtilen ZIP ayrıca bulunmadığı için eşleşen bu arşiv kullanıldı.

## Sonuçlar

Her satır 3.000 test yorumu; her gerçek sınıfta 1.000 yorum. Geçersiz çıktı sayısı bütün koşumlarda sıfırdır.

__RESULTS_TABLE__

İngilizcede BERT accuracy bakımından, Qwen Macro F1 bakımından daha yüksek ölçüldü; Macro F1 farkı küçüktür ve anlamlılık testi yapılmadı. Türkçede BERT toplam accuracy ve Macro F1 bakımından daha yüksektir. Bunlar bu sabit dengeli alt kümenin sonuçlarıdır. Türkçe VADER doğrudan kullanımının adı **tanısal başlangıç deneyi**dir; yerleşik Türkçe desteği olarak yorumlanmaz.

## Kurulum

Proje dizini `sentiment_baslangic` içindeyken Windows PowerShell:

```powershell
$env:PYTHONUTF8 = "1"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch==2.5.1+cu121 --index-url https://download.pytorch.org/whl/cu121
python -m pip install -r requirements-ml-tested.txt vaderSentiment==3.3.2 python-docx==1.2.0
python -m unittest discover -s . -p "test_*.py" -v
python 00_audit.py
```

BERT ve grafikler Python 3.11.1, PyTorch 2.5.1+cu121, Transformers 5.6.1 ile gerçekten çalıştırıldı. Eski `requirements-tested.txt` başlangıç paketinin Python 3.12 ortamıdır; yeni koşumun sürümleri `requirements-ml-tested.txt` içindedir. Genel sürüm aralıkları `requirements-ml.txt` içindedir. Yeni çalışmada mevcut CUDA ortamı yalnızca çalıştırıcı olarak kullanıldı; paketler değiştirilmedi. Asıl yorumlama ortamının yolu her BERT koşumunun `environment.json` kaydındadır. Word, Codex'in paketlenmiş Python ortamındaki python-docx 1.2.0 ile üretildi.

Yalnızca veri ve sonuç kontrolü için standart Python yeterlidir; kurulu model kütüphanesi veya ağ gerekmez. GPU olmayan ortamda BERT `--device cpu` ile çalışabilir; süre uzar. Platforma uygun PyTorch kurulumu için https://pytorch.org/get-started/previous-versions/ adresine bakın.

## Veri sabitleme

Her dilde eğitim 11.400, doğrulama 600, test 3.000; sınıf başına 3.800 / 200 / 1.000. `data/manifest.json` kaynak commitlerini, kaynak ve temiz sınıf sayılarını ve altı dosyanın SHA256 değerlerini taşır. Bölümler geçerlidir ve korunmuştur. Emoji, olumsuzluk, noktalama ve büyük harf silinmez.

```powershell
python 00_audit.py
```

Boş metin, ID tekrarı, normalleştirilmiş tam metin tekrarı, çelişkili etiket, bölüm sızıntısı, resmi İngilizce bölüm sınırları ve hashler kontrol edilir. Ham kaynak bu devam çalışmasında yeniden indirilmedi; kaynak sayıları sabit manifest ve kaynak kartına dayanır. İngilizce eğitimdeki sekiz iç içe HTML entity değiştirilmeden raporlandı. Yakın tekrar, kullanıcı veya ürün düzeyi sızıntı tümüyle dışlanamaz.

Veriyi tekrar üretmek gerekirse **yeni dizin** seçin:

```powershell
python 01_prepare_data.py --output data_reproduced --en-revision b3a375baf0f409c77e6bc7aa35102b7b3534f8be --tr-revision 3bda52ed2c57ac1e80ac463192cafeeae9f72213
```

## VADER

Başlangıç paketinin tahminleri `predictions/`, sonuçları `results/en_vader` ve `results/tr_vader_diagnostic` içindedir. Yeniden hesaplama aynı metrikleri verdi. vaderSentiment 3.3.2, compound ≤−0,05 negatif; ≥0,05 pozitif; arası nötr.

```powershell
python 02_vader.py --input data/en/test.csv --output predictions/en_vader_repeat.csv --language en
python 03_evaluate.py --gold data/en/test.csv --predictions predictions/en_vader_repeat.csv --output results/en_vader_repeat --method VADER --language en
python 02_vader.py --input data/tr/test.csv --output predictions/tr_vader_repeat.csv --language tr --turkish-diagnostic
```

Mevcut çıktıların üzerine yazılmaz. Türkçe doğrudan sonuç dil uyumsuzluğunu ölçer.

## BERT fine tuning

Başlangıç adayları kullanıldı: EN `google-bert/bert-base-uncased`, TR `dbmdz/bert-base-turkish-cased`. Üç sınıflı başlık eğitim verisinde fine tuning gördü. LR 2e-5, batch 16, max length 256, en fazla 3 epoch, seed 42. Checkpoint validation Macro F1 ile seçildi; test eğitim tamamlandıktan sonra okundu. Test etiketleri çıkarım girdisinde bulunmaz.

```powershell
python 04_bert.py --language en --run-dir runs/en_bert_repeat --revision 86b5e0934494bd15c9632b12f734a8a67f723594
python 04_bert.py --language tr --run-dir runs/tr_bert_repeat --revision b6e1de16c983e0f2c70664591ea3f22810072608
```

Ana gerçek koşumlar `runs/en_bert_seed42` ve `runs/tr_bert_seed42` dizinlerindedir. `config.json`, `environment.json`, `history.json`, `selection.json`, `training_complete.json`, `test_predictions.csv` ve `evaluation/` kayıtları bulunur. En iyi model/tokenizer `best/` altındadır. Etiket sırası negative/neutral/positive olarak sabittir. Model kartları ve güncel AutoTokenizer / AutoModelForSequenceClassification API'ları doğrulanıp gerçek koşumla sınandı.

Bellek yetersizse yeni koşumda `--batch-size 8 --gradient-accumulation 2` etkin batch 16 sağlar. Ayarlar metadata'ya yazılır. Eğitim epoch sınırındaki `resume.pt` dosyasından aynı ayarlarla `--resume` ile devam eder; yarım epoch yeniden yapılır. `--predict-only` tamamlanmış fine tuning olmadan çalışmaz. `--smoke` sadece yazılım denemesidir; test tahmini üretmez ve proje sonucu sayılmaz.

İsteğe bağlı üç seed tekrarını testten önce kararlaştırılmış aynı ayarlarla çalıştırabilirsiniz:

```powershell
foreach ($seed in 13, 42, 2026) {
  python 04_bert.py --language en --seed $seed --run-dir "runs/en_bert_seed${seed}_replicate" --revision 86b5e0934494bd15c9632b12f734a8a67f723594
  python 04_bert.py --language tr --seed $seed --run-dir "runs/tr_bert_seed${seed}_replicate" --revision b6e1de16c983e0f2c70664591ea3f22810072608
}
```

Bu tekrarlar **çalıştırılmadı**. Ana rapor tek seed içerir. Tekrarların test puanına göre seed seçilmez; hepsi birlikte raporlanır.

## Yerel LLM

İki dilde aynı instruction tuned `qwen2.5:latest` 7B Q4_K_M ağırlıkları kullanıldı. Değişebilir tag yerine gerçek digest kaydedildi: `845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e`.

Ollama servisi açık olmalıdır. Bu model deney makinesinde zaten yüklüydü; yeni makinede `ollama pull qwen2.5:7b` ile edinilen ağırlığın digest'ini doğrulayın ve yapılandırmadaki model adını ayarlayın. Farklı tag aynı digest'e sahip olmayabilir. `configs/llm_local.json` iki dilde ortaktır. Temperature 0, seed 42, 4096 bağlam, 16 çıktı tokenı, timeout 90 saniye, en fazla 3 deneme.

Temiz tekrar için dört yeni koşum dizininin aynı kökte olması gerekir:

```powershell
python 05_llm.py --language en --stage pilot --run-dir runs_repeat/en_llm_pilot --workers 2
python 05_llm.py --language tr --stage pilot --run-dir runs_repeat/tr_llm_pilot --workers 2
python 05_llm.py --language en --stage test --run-dir runs_repeat/en_llm_test --pilot-root runs_repeat --workers 2
python 05_llm.py --language tr --stage test --run-dir runs_repeat/tr_llm_test --pilot-root runs_repeat --workers 2
```

Her pilot validation'dan sınıf başına 10 yorum içerir. Testten prompt seçilmez. Aynı prompt ve sınıf tanımları iki dilde korunur. Her yorum bağımsız istektir. İstek gövdesinde yalnızca metin vardır; altın etiket ve kaynak puan gönderilmez. `records.jsonl` her yorumun ID, tahmin, ham yanıt, bütün denemeler, süre ve token kullanımını saklar. Yalnızca üç tam küçük harfli etiket geçerlidir. Başarısız yanıt `__invalid__` kalır; nötre dönüştürülmez ve değerlendirme paydasında tutulur.

Kesintide aynı komuta `--resume` ekleyin. Logun sadece yarım son satırı güvenle onarılabilir. ID, girdi hash'i, model ağırlığı, chat template ve prompt değişirse devam engellenir. Deneyde Türkçe koşum 2.318 kayıt sonrası servis güncellemesinde kesildi; ağırlık ve prompt sabit tutularak kalan 682 kayıt `--resume --allow-runtime-version-change` ile tamamlandı. Bu açık seçenek yalnızca çalıştırıcı sürümünü değişmeye bırakır; model digest veya girdi değişikliğine izin vermez. Ollama 0.40.15 / 0.40.16 ayrımı metadata ve raporda yazılıdır.

## API seçeneği ve maliyet onayı

`configs/llm_api.example.json` OpenAI uyumlu chat completions şeması içindir. Gerçek çok dilli instruction model snapshot kimliğini, endpoint'i ve ortam değişkeni adını ayarlayın. Anahtarı yalnızca `SENTIMENT_LLM_API_KEY` gibi bir ortam değişkeninden verin; dosyaya yazmayın. API sağlayıcısının modeli ve sınıf davranışı yeni validation pilotuyla doğrulanmalıdır.

Önce sağlayıcının **güncel** 1 milyon token fiyatlarını girerek, ağı aramadan maliyet tahmini üretin:

```powershell
python 05_llm.py --config configs/my_api.json --language en --stage pilot --run-dir runs_api/en_llm_pilot --estimate-only --input-usd-per-million GUNCEL_GIRIS_FIYATI --output-usd-per-million GUNCEL_CIKIS_FIYATI
```

`cost_estimate.json` UTF8 byte sayısı ve çerçeve payıyla üst bütçe yaklaşımını, max output ve bütün retry'ları içerir; kesin fatura değildir. Ücretli toplu çalışma öncesi tahmin kullanıcıya gösterilip açık onay alınmalıdır. Onaylanan aynı tahminin `approval_hash` değeri `--approve-estimate-sha256 HASH` ile verilmedikçe hiçbir API isteği gönderilmez. Fiyat değerleri yer tutucudur; gerçek bir fiyat veya maliyet uydurulmamıştır. Bu projede ücretli API çağrısı yapılmadı.

## İsteğe bağlı çeviri ve VADER

`06_translate_vader.py` ayrı bir Türkçe → İngilizce model + orijinal VADER hattıdır. Bu deney **çalıştırılmadı**. Model ve tokenizer revision, çevrilmiş metinler, batch süreleri, girdi kesilmesi ve VADER sürümü kaydedilir. Çeviri anlam ve duygu değiştirebilir.

```powershell
python -m pip install sentencepiece sacremoses
python 06_translate_vader.py --run-dir runs/tr_translation_vader --model Helsinki-NLP/opus-mt-tr-en
```

Modelin yalnızca eski PyTorch `.bin` ağırlıkları varsa güncel Transformers, torch 2.6 veya üzeri isteyebilir. Bu isteğe bağlı deney için ayrı güncel bir ortam kullanın; çalıştırılmış BERT ortamını değiştirmeyin. 512 kaynak token kesme ve 4 beam ayarları kayıtlıdır. Türkçe ana altı satırda doğrudan tanısal VADER bulunur; çeviri sonucu oraya gizlice eklenmez.

## Ortak değerlendirme ve rapor

Özgün `03_evaluate.py` korunmuştur. Tüm yeni yöntemler aynı değerlendiriciyi kullanır. Eksik/fazla/tekrar ID, beklenmedik etiket ve hash uyumsuzluğu hata üretir. Yanlış(c) = gerçek c toplamı − doğru c. Karışıklık matrisi gerçek sınıf satırları ve tahmin sütunlarıyla, geçersiz için ek sütunla kaydedilir. Her yöntemde `metrics.json`, `class_errors.csv`, `confusion_matrix.csv`, `misclassified.csv` vardır.

```powershell
python 07_build_results.py
python 11_write_guides.py
python 08_write_report.py
python 09_verify_delivery.py
python 10_package.py --output ../Duygu_Analizi_Teslim_Tekrar.zip
```

Karşılaştırma üreticisi ana `runs/*_bert_seed42` ve `runs/*_llm_test` dizinlerini kullanır. Yeni deneyler için bu yolları bilinçli biçimde yapılandırın; eski sonuçların üzerine yazmayın. Eksik sonuç varsa 07 normalde durur; `--allow-partial` yalnızca eksikleri açıkça işaretleyen ara rapor içindir. Word raporunun son hali bütün altı ölçümü içerir. Grafik ve tablo yenilemesi eski tahminleri yeniden çalıştırmaz.

Hata inceleme dosyaları: sınıf başına 5 yanlış/dil/yöntem, toplam 90 gerçek örnek `error_review_sample.csv` içindedir. Regex ile bulunan `error_candidates.csv` etiketlenmiş hata kategorileri değildir. Beş açıklamalı vaka `error_case_studies.csv` içindedir; kategori sıklığını temsil etmez. Testin altın etiketleri değiştirilmez. İki insanın bağımsız incelemesi için alanlar boştur.

Word görsel denetimi için bu Windows ortamında paketli LibreOffice yoktu. Standart `render_docx.py` bu nedenle çalışamadı; rapor görünmez Microsoft Word oturumunda PDF'e çevrilip tüm sayfalar PNG olarak incelendi. Bunlar `qa/` altındaki ara çıktılardır. İsteğe bağlı aynı yerel yol:

```powershell
.\tools\render_word.ps1 -InputDocx deliverables\Proje_Raporu.docx -OutputPdf qa\report\Proje_Raporu.pdf
python tools\render_pdf_pages.py qa\report\Proje_Raporu.pdf qa\report\pages
```

İkinci komut için `pypdfium2` gerekir; rapor metrik üretiminin bağımlılığı değildir.

## Paket sınırı ve sınırlılıklar

Teslim ZIP'i kod, sabit veriler, gerçek tahminler, loglar, değerlendirmeler, Word, konuşma taslağı ve kaynak kayıtlarını içerir. Büyük model ağırlıkları, `resume.pt`, önbellek ve QA ara görüntüleri ZIP'e konmaz. Eğitilmiş ağırlıklar bu çalışma klasöründe `runs/*_bert_seed42/best` altında korunur; hashleri `audit/model_artifacts.json` içindedir. Ağırlıkların ayrıca istenmesi halinde bu klasörler teslim dizinine ayrıca eklenmelidir.

İngilizce sosyal medya ile Türkçe ürün yorumları farklı alanlardır. BERT denetimli, Qwen zero shot'tır. Açık veriyle ön eğitim çakışması, etiket gürültüsü, tek seed, nötr sınıf tanımı ve Türkçe koşumda çalıştırıcı güncellemesi sınırlılıktır. BERT optimizasyon ve test çıkarım süreleri ayrıdır; ilk koşumun indirme/veri kodlama/checkpoint yazma dahil tam duvar süresi ölçülmemiştir. Türkçe LLM ilk oturumunun tam duvar süresi kayboldu; her yorumun gecikmesi korundu ve son oturum ayrıca ölçüldü. Makro F1 farklarının istatistiksel anlamlılığı hesaplanmadı.

## Kaynaklar

Veri kartları: https://huggingface.co/datasets/cardiffnlp/tweet_eval ve https://huggingface.co/datasets/maydogan/Turkish_SentimentAnalysis_TRSAv1

BERT kartları: https://huggingface.co/google-bert/bert-base-uncased ve https://huggingface.co/dbmdz/bert-base-turkish-cased

Qwen: https://huggingface.co/Qwen/Qwen2.5-7B-Instruct ve https://ollama.com/library/qwen2.5:latest

VADER: https://github.com/cjhutto/vaderSentiment

API: https://huggingface.co/docs/transformers/en/tasks/sequence_classification ve https://docs.ollama.com/api/chat

Tam kaynakça Word raporunda, erişim kayıtları `audit/sources_verified.json` içindedir. Kaynaklar 18 Kasım 2026 tarihinde doğrulandı.
'''
    (ROOT / "README.md").write_text(readme.replace("__RESULTS_TABLE__", table), encoding="utf-8")
    status = "# Gerçek çalıştırma durumu\n\nTarih 18 Kasım 2026. Yalnızca gerçek ölçümler yazılmıştır.\n\n"
    status += "## Tamamlananlar\n\n- Özgün arşivin 31 dosyayla eşleşmesi ve yedeği.\n- Her dilde 15.000 sabit metin; altı bölümün hash ve sızıntı denetimi.\n- Önceki beş Python dosyası, manifest, veriler ve VADER çıktıları korunarak metriklerin doğrulanması.\n- İki BERT modelinin seed 42 ile üç epoch fine tuning eğitimi; validation Macro F1 ile seçilen checkpointler.\n- Her dilde 30 validation yorumuyla LLM pilotu; aynı Qwen ağırlıkları ve promptla iki tam test.\n- Altı koşumda 18.000 ID eşleşmiş test tahmini; geçersiz çıktı sıfır.\n- 14 anlamlı yazılım testi; veri, kayıt, model ve prompt kimliği denetimleri.\n- Sınıf metrikleri, hata yönleri, karışıklık matrisleri, yanlış yorum CSV'leri ve gerçek grafikler.\n- Türkçe Word raporu, beş açıklamalı gerçek hata vakası ve 90 örneklik insan inceleme listesi.\n- Üç kişi için toplam 9 dakikalık sunum akışı ve konuşma taslağı.\n\n## Gerçek test sonuçları\n\n" + table
    status += "\n## Koşullar ve kesinti\n\nBERT: RTX 3080 Ti 12 GB; batch 16, LR 2e-5, max length 256, 3 epoch, seed 42, FP16. Her iki dilde seçilen epoch 3. EN validation Macro F1 0.7469; TR 0.8511. EN optimizasyon 116.54 s ve test çıkarımı 2.46 s; TR 119.63 s ve 2.74 s. Bu optimizasyon süresi indirme, kodlama ve checkpoint yazmayı kapsamaz.\n\nLLM: Qwen2.5 7B Instruct Q4_K_M; prompt hash 06cbb38c59dab736259c3a15e4c1daa100aadf38e40c7c0a5615843ba4236091. Bu hash yapılandırma ile promptun ortak deney hashidir. Aynı model digest iki dilde korundu. EN pilot Macro F1 0.5477; TR pilot 0.7629. Prompt değiştirilmedi. EN test Ollama 0.40.15; TR ilk 2.318 kayıt 0.40.15 ve kalan 682 kayıt 0.40.16 ile, kayıtlar korunarak tamamlandı. Güncelleme yalnızca çalıştırıcıya aittir; ağırlık digest, chat template ve prompt değişmedi. Sürüm farkı sınırlılık olarak raporlandı. Yerel çalışma için sağlayıcı API ücreti yok; enerji maliyeti ölçülmedi.\n\nİngilizce test LLM duvar süresi 89.56 s; istek gecikmeleri toplamı 178.91 s. Türkçe son oturum 41.79 s; bütün yorumların gecikme toplamı 507.23 s. İki paralel istek nedeniyle toplam gecikme duvar süresine eşit değildir. Türkçe ilk oturumun tam duvar süresi kesintide kaydedilemedi.\n\n## Çalıştırılmayan ve insana ait işler\n\n- İsteğe bağlı Türkçe çeviri ve VADER hattı: kod hazır, deney yapılmadı.\n- Üç seed BERT tekrarı: komutlar hazır, çalıştırılmadı.\n- Ücretli API: yapılandırılabilir çalıştırıcı ve maliyet onay kapısı var; gerçek API çağrısı yapılmadı.\n- İki grup üyesinin bağımsız hata kodlaması yapılmadı.\n- Tam üç üyenin adları ve öğrenci numaraları ile ders bilgileri eksik.\n- Konuşma taslağı video değildir; video kaydı yapılmadı.\n- E posta, bulut paylaşımı, elden teslim veya gerçek gönderim yapılmadı.\n\n## Kanıt dosyaları\n\n`audit/data_integrity.json`, `audit/archive_verification.json` yerine arşiv için `provenance/archive_verification.json`, `audit/delivery_validation.json`, `audit/model_artifacts.json`, `data/manifest.json`, `runs/*/config.json`, `runs/*/history.json`, `runs/*/evaluation/metrics.json`, `runs/*llm*/records.jsonl` ve `deliverables/comparison.csv`. Word sayfalarının görsel denetimi `audit/document_visual_qa.json` kaydında belirtilir.\n"
    status = status.replace("`audit/archive_verification.json` yerine arşiv için ", "")
    if group:
        status = status.replace("Tam üç üyenin adları ve öğrenci numaraları ile ders bilgileri eksik.",
                                "Üç grup üyesinin adı, öğrenci numaraları, ders ve öğretim elemanı bilgileri yerel teslim raporunda tamamlandı. GitHub kopyasında öğrenci numaraları gizlidir.")
    (ROOT / "CALISTIRMA_DURUMU.md").write_text(status, encoding="utf-8")
    speech = '''# Üç kişilik sunum akışı ve konuşma taslağı

Hedef süre **9 dakika**, üst sınır **10 dakika**. Tam üç konuşmacı; her biri yaklaşık üç dakika. Bu dosya konuşma taslağıdır; video kaydı değildir. İsimler ve öğrenci numaraları grupta doldurulacak. Prova süresine göre örnek sayısını azaltın; sayıları veya sınırlılıkları değiştirmeyin.

| Zaman | Konuşmacı | Gösterilecek içerik |
|---|---|---|
| 00:00–01:00 | Üye 1 | Amaç ve veri kaynakları |
| 01:00–02:00 | Üye 1 | Dengeli bölümler ve sızıntı kontrolü |
| 02:00–03:00 | Üye 1 | Deney tasarımı ve metrikler |
| 03:00–04:00 | Üye 2 | VADER ve Türkçe tanısal kullanım |
| 04:00–05:00 | Üye 2 | BERT eğitimi ve checkpoint seçimi |
| 05:00–06:00 | Üye 2 | Karşılaştırma tablosu ve sınıf hataları |
| 06:00–07:00 | Üye 3 | LLM pilotu ve test koşulları |
| 07:00–08:00 | Üye 3 | Gerçek hata örnekleri |
| 08:00–09:00 | Üye 3 | Sınırlılıklar ve kapanış |

## Üye 1 için konuşma taslağı 00:00–03:00

Bu çalışmada İngilizce ve Türkçe metinlerde negatif, nötr ve pozitif duygu sınıflandırmasını üç yöntemle karşılaştırdık. VADER bir sözlük ve kural sistemi, BERT etiketli veriyle eğitilen bir dil modeli, Qwen ise temel deneyde örnek gösterilmeden kullanılan büyük dil modelidir. Amacımız yalnızca tek bir başarı yüzdesi bulmak değildi. Hangi gerçek sınıfın başka hangi sınıfa karıştığını da ölçtük.

İngilizce kaynak CardiffNLP TweetEval’in sentiment bölümüdür ve sosyal medya metinleri içerir. Türkçe kaynak TRSAv1 ürün yorumlarıdır. Kaynak sınıflarının her biri en az bin yorum koşulunu karşılar. Türkçe kaynağın ilk hali her sınıfta elli bin yorum içerir. İngilizce kaynak sayıları, veri sürümleri ve hashler manifestte kayıtlıdır. Bu iki alan farklı olduğu için sonuçlar arasındaki farkı yalnızca dile bağlayamayız.

Her dilde eğitimde on bir bin dört yüz, doğrulamada altı yüz, testte üç bin metin kullandık. Sınıf başına bunlar üç bin sekiz yüz, iki yüz ve bin örnektir. Bölümler daha önce hazırlanmıştı; yeniden örnekleme yapmadık. Boş metni, tam tekrarları, çelişkili etiketleri ve bölümler arasında aynı metnin geçmesini denetledik. Otuz bin satırın ve altı dosyanın bütünlüğü doğrulandı. Emoji, büyük harf, noktalama ve olumsuzluk sözcükleri korundu.

BERT yalnızca eğitim etiketleriyle öğrendi. Doğrulama verisi checkpoint seçimi için kullanıldı. LLM pilotu da doğrulama verisinde yapıldı. Testten prompt veya hiperparametre seçmedik. Aynı dilde üç yöntem tam olarak aynı test ID’lerine tahmin verdi; satır sırası üzerinden eşleştirme yapmadık. Test etiketlerini modele göndermedik.

Accuracy doğru sayısının toplam örneğe oranıdır. Macro F1 ise üç sınıfın F1 değerlerinin ortalamasıdır. Sınıfın yanlış sayısını, gerçek etiketi o sınıf olan bin örnekten doğru bulunanları çıkararak hesapladık. Geçersiz cevap olsaydı paydadan çıkarmayacaktık. Şimdi arkadaşım VADER ve BERT sonuçlarını anlatacak.

## Üye 2 için konuşma taslağı 03:00–06:00

VADER’da orijinal vaderSentiment üç nokta üç nokta iki sürümünü ve standart compound eşiklerini kullandık. Eksi sıfır virgül sıfır beş ve altı negatif, artı sıfır virgül sıfır beş ve üstü pozitif, arası nötrdür. İngilizce testte accuracy yüzde 56,07, Macro F1 0,5564 çıktı. Gerçek negatif sınıfta 447, nötr sınıfta 579, pozitif sınıfta 292 hata var.

VADER’ın standart sözlüğü İngilizcedir. Bu nedenle Türkçeye doğrudan uygulamayı tanısal başlangıç deneyi olarak adlandırdık. Türkçe destekli bir sistemmiş gibi sunmuyoruz. Üç bin Türkçe yorumun iki bin yedi yüz yetmiş ikisini nötr tahmin etti. Accuracy yüzde 36,77 ve Macro F1 0,2534. Yüksek nötr recall, diğer sınıfların nötre yığılmasını gizlememeli. Çeviri ve VADER için ayrı bir çalıştırıcı hazırladık; bu ek deney yapılmadığı için sonuç yazmadık.

BERT tarafında İngilizcede bert base uncased, Türkçede BERTurk cased başlangıç modellerini kullandık. Üç sınıflı başlık ekleyip bütün parametreleri eğitim verisinde güncelledik. Öğrenme oranı iki çarpı on üzeri eksi beş, batch on altı, uzunluk iki yüz elli altı token, en fazla üç epoch ve seed kırk ikidir. Modellerin commitleri ve tokenizer sürümleri kaydedildi.

İki dilde de en iyi checkpoint üçüncü epoch oldu; karar yalnızca validation Macro F1 ile verildi. Teste göre yeniden eğitim ayarı seçmedik. RTX 3080 Ti üzerinde İngilizce optimizasyon yaklaşık 116,5, Türkçe 119,6 saniye sürdü; bu süreler indirme ve checkpoint yazmayı kapsamıyor.

İngilizce BERT accuracy yüzde 69, Macro F1 0,6843 verdi. Negatif yanlış sayısı 148’e indi; nötrde 497 hata kaldı. Türkçe BERT accuracy yüzde 82,30, Macro F1 0,8234 verdi; sınıf hataları negatifte 150, nötrde 240 ve pozitifte 141 oldu. Karışıklık matrisleri hangi sınıfın nereye gittiğini gösteriyor. İngilizcede Qwen’in Macro F1 değeri BERT’ten çok az yüksek, accuracy değeri ise biraz düşük. Bu küçük fark için anlamlılık testi yapmadık. Arkadaşım LLM koşumunu ve hata örneklerini açıklayacak.

## Üye 3 için konuşma taslağı 06:00–09:00

İki dilde aynı yerel Qwen2.5 yedi milyarlık instruction modelini kullandık. Model test sonuçları görülmeden, bilgisayarda bulunduğu ve on iki gigabayt GPU’ya sığdığı için seçildi. Ağırlık digest’i iki dilde aynıdır. Prompt ve sınıf tanımları da aynıdır. Her dilde validation’dan sınıf başına on, toplam otuz yorumla pilot yaptık; promptu değiştirmeden tam teste geçtik.

Modelden sadece negative, neutral veya positive kabul ettik. Her yorumun ID’sini, ham yanıtını, gecikmesini, bütün denemeleri ve token kullanımını kaydettik. Timeout ve tekrar deneme desteği ekledik. Hatalı cevapları nötre çevirmiyoruz; ayrı geçersiz çıktı olarak tutuyoruz. Tam testlerde geçersiz çıktı çıkmadı. Ücretli API çağrısı yapılmadı; yerel model kullanıldı.

İngilizce Qwen accuracy yüzde 68,30 ve Macro F1 0,6867 verdi. Türkçe accuracy yüzde 73,67 ve Macro F1 0,7187. Türkçe negatifte yalnızca 106, pozitifte 115 hata varken nötrde 569 hata var. Bu nedenle tek bir ortalama puan sınıf davranışını yeterince açıklamıyor.

Örneğin “kokusu çok güzel ama saçımda bir etkisini görmedim” yorumunun kaynak etiketi pozitif, BERT ve Qwen tahmini nötrdür. Aynı metin hem beğeni hem olumsuz deneyim içerir. “Abarttıkları kadar olmasada idare eder bir ürün” kaynakta negatifken Qwen nötr demiştir. Bunlar nötr sınıf sınırını tartışmaya açar. “Aşırı iyi ürün herkese almasını tavsiye ederim” metninin kaynakta negatif olması olası etiket gürültüsüdür; bağımsız inceleme olmadan kesin hata demiyoruz. Altın etiketleri değiştirmedik. İroni ve olumsuzluk örnekleri de raporda var.

Sınırlılıklarımız şunlar: iki dilin alanları farklı, BERT denetimli ama Qwen zero shot, ana eğitim tek seed içeriyor ve açık verinin ön eğitimde görülmediği garanti edilemiyor. Türkçe LLM koşumu servis güncellemesiyle kesildi; ilk 2318 tahmin korundu, kalan 682 aynı ağırlık ve promptla tamamlandı. Ollama 0.40.15 ve 0.40.16 farkını raporladık.

Bu sabit testte Türkçe BERT en yüksek genel Macro F1’i verdi. İngilizcede accuracy ve Macro F1 sıralaması farklılaşabiliyor. Kullanım kararı verirken gerçek sınıf hatalarını, eğitim koşullarını ve süreleri birlikte değerlendirmek gerekiyor. Kodlar, sabit veriler, gerçek sonuçlar ve çalıştırma komutları teslim paketinde bulunuyor.

## Prova ve kayıt notları

Metni doğal konuşma hızınızla prova edin. Konuşmacı geçişleri dahil süreyi ölçün; toplam 10 dakikayı aşarsa yöntem açıklamalarını kısaltın. Grafiklerde sınıf ve yöntem adlarını okunur büyüklükte gösterin. Üç kişi de aktif konuşmalı. Dosya, video kaydı veya gerçek teslim yapılmış olduğunu göstermez.
'''
    if group:
        speech = speech.replace("İsimler ve öğrenci numaraları grupta doldurulacak.", "Konuşmacı adları aşağıdaki önerilen akışa yerleştirildi; bu bir video kaydı değildir.")
        for i, member in enumerate(group["members"], 1):
            speech = speech.replace(f"Üye {i}", member["name"])
    (ROOT / "deliverables/SUNUM_VE_KONUSMA_TASLAGI.md").write_text(speech, encoding="utf-8")
    checklist = '''# Teslim kontrol listesi

Teslim tarihi **25 Kasım 2026 Çarşamba ders saatidir**. Grup tam üç kişi olmalıdır. **İmza karşılığı derste elden ve e-posta ile teslim birlikte zorunludur.**

- [x] Sabit train validation test dosyaları ve manifest korundu.
- [x] Her dilde üç yöntem aynı 3.000 test ID’sinde değerlendirildi.
- [x] İki BERT fine tuning koşumu ve LLM validation pilotları tamamlandı.
- [x] 18.000 gerçek test tahmini ve ham LLM kayıtları saklandı.
- [x] Accuracy Macro F1 sınıf hataları hata oranları precision recall F1 ve karışıklık matrisleri üretildi.
- [x] Yanlış yorum CSV’leri ve geçersiz çıktı denetimleri hazırlandı.
- [x] Türkçe tanısal VADER ve alan farkı sınırlılıkları açıklandı.
- [x] Çalıştırıcı güncellemesi ve kesintiden devam etme raporlandı.
- [x] 14 yazılım testi geçti; veri ve ID denetimleri tamamlandı.
- [x] Türkçe Word raporu gerçek sonuçlarla oluşturuldu.
- [x] Üç kişi için 9 dakikalık konuşma akışı ve taslağı hazırlandı.
- [x] Kurulum ve tekrar üretme komutları README’ye yazıldı.
- [ ] Üç üyenin adı soyadı ve öğrenci numarasını rapora ekleyin.
- [ ] Ders ve öğretim elemanı bilgilerini doğrulayın.
- [ ] İki üye error_review_sample.csv dosyasını bağımsız inceleyip katkılarını kaydetsin.
- [ ] Üç kişinin aktif konuştuğu en fazla 10 dakikalık videoyu kaydedin ve süreyi kontrol edin.
- [ ] Son ZIP’i başka bir klasöre açıp rapor ve CSV dosyalarını kontrol edin.
- [ ] Hoca model ağırlıklarını isterse runs/*_bert_seed42/best klasörlerini ayrıca ekleyin; büyük ağırlıklar küçük teslim ZIP’inde yoktur.
- [ ] Teslim biçimini ve alıcı bilgilerini dersin gerçek yönergesiyle doğrulayın.
- [ ] Word raporu, kaynak kodları ve herkesin aktif yer aldığı en fazla 10 dakikalık videoyu e-posta ile gönderin.
- [ ] E-posta eklentisi boyut sınırına takılırsa bütün materyalleri OneDrive klasörüne koyun; erişim bağlantısını e-postaya ekleyip alıcı erişimini doğrulayın.
- [ ] 25 Kasım Çarşamba ders saatinde imza karşılığında elden teslimi tamamlayın.

GitHub deposunun paylaşılması, e-posta ve imza karşılığı elden teslimin yerine geçmez. Güncel gereksinim eşleştirmesi [ödev uygunluk kontrolündedir](ODEV_UYGUNLUK_KONTROLU.md).

Çeviri ve VADER ile üç seed tekrarları isteğe bağlıdır; çalıştırılmadı. Bu liste video, paylaşım veya gerçek teslimin yapıldığı anlamına gelmez.
'''
    if group:
        checklist = checklist.replace("- [ ] Üç üyenin adı soyadı ve öğrenci numarasını rapora ekleyin.", "- [x] Üç üyenin adı soyadı ve öğrenci numarası yerel teslim raporuna eklendi; GitHub kopyasında numaralar gizli.")
        checklist = checklist.replace("- [ ] Ders ve öğretim elemanı bilgilerini doğrulayın.", "- [x] BİM 448 Veri Madenciliği ve Bilgi Keşfi ve Doç. Dr. Aysun Güran bilgileri kapağa eklendi.")
        checklist += "\nE-posta ve elden teslim için tam kapaklı yerel `teslim_ozel/Proje_Raporu.docx` dosyasını kullanın. GitHub raporu öğrenci numaralarını içermez.\n"
    (ROOT / "deliverables/TESLIM_KONTROL_LISTESI.md").write_text(checklist, encoding="utf-8")
    sources = [
        ("TweetEval dataset card", "https://huggingface.co/datasets/cardiffnlp/tweet_eval"),
        ("TRSAv1 dataset card", "https://huggingface.co/datasets/maydogan/Turkish_SentimentAnalysis_TRSAv1"),
        ("TRSAv1 original paper", "https://journals.sagepub.com/doi/10.1177/01655515221074328"),
        ("TweetEval paper", "https://aclanthology.org/2020.findings-emnlp.148/"),
        ("BERT paper", "https://aclanthology.org/N19-1423/"),
        ("English BERT model card", "https://huggingface.co/google-bert/bert-base-uncased"),
        ("Turkish BERT model card", "https://huggingface.co/dbmdz/bert-base-turkish-cased"),
        ("Qwen2.5 instruction model card", "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct"),
        ("Ollama model quantization", "https://ollama.com/library/qwen2.5:latest"),
        ("VADER original implementation", "https://github.com/cjhutto/vaderSentiment"),
        ("Transformers classification API", "https://huggingface.co/docs/transformers/en/tasks/sequence_classification"),
        ("Ollama chat API", "https://docs.ollama.com/api/chat"),
        ("Optional translation model card", "https://huggingface.co/Helsinki-NLP/opus-mt-tr-en"),
        ("PyTorch CUDA 12.1 installation for 2.5.1", "https://pytorch.org/get-started/previous-versions/")]
    write_json(ROOT / "audit/sources_verified.json", {"access_date": "2026-11-18", "sources": [{"title": t, "url": u} for t, u in sources],
                                                     "verification": "Primary source pages reviewed; model APIs additionally validated by real BERT/Ollama runs."})
    # Keep all three methods represented in the five qualitative cases.
    case_path = ROOT / "deliverables/error_case_studies.csv"
    cases = read_csv(case_path)
    for case in cases:
        if case["category"] == "Nötr sınıf sınırı":
            pred = next(r for r in read_csv(ROOT / "runs/tr_llm_test/predictions.csv") if r["id"] == case["id"])
            if pred["prediction"] != case["label"]:
                case["method"] = "Qwen 2.5 7B"
                case["prediction"] = pred["prediction"]
    write_csv(case_path, cases, ("category", "language", "method", "id", "text", "label", "prediction", "interpretation"))
    from experiment_utils import load_script
    load_script("12_build_readme.py").main()
    print("Updated README, run status, presentation script, checklist and source records")


if __name__ == "__main__":
    main()
