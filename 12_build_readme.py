"""Build the visual GitHub README from measured results and verified real cases."""
import json
from pathlib import Path

from common import LABELS, read_csv
from experiment_utils import ROOT

START = "<!-- RUN_GUIDE_START -->"
END = "<!-- RUN_GUIDE_END -->"


def fmt(value, places=4):
    return f"{float(value):.{places}f}".replace(".", ",")


def main():
    current = (ROOT / "README.md").read_text(encoding="utf-8")
    group_path = ROOT / "configs/group_members.public.json"
    group = json.loads(group_path.read_text(encoding="utf-8")) if group_path.exists() else None
    if START in current and END in current:
        guide = current.split(START, 1)[1].split(END, 1)[0].strip()
    else:
        guide = "## Kurulum" + current.split("## Kurulum", 1)[1]
        guide = guide.split("## Kaynaklar", 1)[0].strip()
    guide = guide.replace("## Paket sınırı ve sınırlılıklar", "## Paylaşılan dosyalar ve sınırlılıklar")
    old = "Teslim ZIP'i kod, sabit veriler, gerçek tahminler, loglar, değerlendirmeler, Word, konuşma taslağı ve kaynak kayıtlarını içerir. Büyük model ağırlıkları, `resume.pt`, önbellek ve QA ara görüntüleri ZIP'e konmaz. Eğitilmiş ağırlıklar bu çalışma klasöründe `runs/*_bert_seed42/best` altında korunur; hashleri `audit/model_artifacts.json` içindedir. Ağırlıkların ayrıca istenmesi halinde bu klasörler teslim dizinine ayrıca eklenmelidir."
    new = "GitHub deposu kod, sabit veriler, gerçek tahminler, deney kayıtları, değerlendirmeler, Word raporu ve konuşma taslağını içerir. Hazırlanan teslim ZIP'i GitHub'a yüklenmemiştir. Büyük model ağırlıkları, `resume.pt`, önbellek ve QA ara görüntüleri de depoya dahil değildir. Eğitilmiş ağırlıklar özgün çalışma bilgisayarında korunur; hashleri `audit/model_artifacts.json` içindedir. Modeller sabit kaynak revision değerleriyle yeniden eğitilebilir."
    guide = guide.replace(old, new)
    rows = read_csv(ROOT / "deliverables/comparison.csv")
    if len(rows) != 6 or any(int(row["n"]) != 3000 for row in rows):
        raise ValueError("README requires all six complete 3000-row test experiments")
    cases = read_csv(ROOT / "deliverables/error_case_studies.csv")
    table = "| Dil | Yöntem | Negatif yanlış | Nötr yanlış | Pozitif yanlış | Accuracy | Macro-F1 |\n|---|---|---:|---:|---:|---:|---:|\n"
    for row in rows:
        name = row["method"] + (" ¹" if row["language"] == "tr" and "VADER" in row["method"] else "")
        table += (f"| {row['language'].upper()} | {name} | {row['negative_incorrect']} | {row['neutral_incorrect']} | "
                  f"{row['positive_incorrect']} | %{fmt(float(row['accuracy'])*100, 2)} | {fmt(row['macro_f1'])} |\n")
    intro = r'''# İngilizce ve Türkçe metinlerde duygu analizi

**VADER · BERT · Qwen 2.5 7B**

İngilizce ve Türkçe metinlerde kural tabanlı, denetimli ve büyük dil modeli temelli duygu analizini karşılaştıran üniversite projesi. Her dilde **negatif, nötr ve pozitif** sınıfları aynı test ID'leri üzerinde değerlendirildi. Sonuçlar gerçek koşumlardan üretilmiştir.

**30.000 metin · 6 temel deney · 18.000 test tahmini · 14 başarılı yazılım testi**

[Sonuçlar](#gerçek-deney-sonuçları) · [Sınıf hataları](#sınıflara-göre-hatalar) · [Hata örnekleri](#gerçek-yorumlarla-hata-incelemesi) · [Kurulum](#kurulum-ve-yeniden-üretme) · [Kaynaklar](#kaynaklar)

[Tez düzeninde akademik Word raporu](deliverables/Proje_Raporu_Tez.docx) · [Kısa rapor](deliverables/Proje_Raporu.docx) · [3 kişilik sunum taslağı](deliverables/SUNUM_VE_KONUSMA_TASLAGI.md) · [Ham sonuç tablosu](deliverables/comparison.csv)

## Tez düzeninde akademik rapor

Genişletilmiş rapor **8 bölüm, 33 kaynak, 9 sayısal tablo, 7 grafik ve 6 denklem** içerir. Türkçe özet, İngilizce abstract, güncel içindekiler, literatür incelemesi, araştırma soruları, veri ve yöntem ayrıntıları, sınıf bazlı sonuçlar, gerçek hata vakaları, geçerlilik tartışması ve deney kimliklerini içeren ekler birlikte sunulur. Ana anlatı ve özetler yaklaşık **6.300 sözcüktür**.

**Akademik yorum:** İngilizce BERT ve Qwen'in küçük farkı için istatistiksel üstünlük iddia edilmez. Türkçede BERT'in toplam 259 örneklik avantajı, nötr sınıftaki 329 örneklik kazanım ile diğer iki sınıftaki toplam 70 örneklik kaybın bileşimidir. Türkçe VADER tanısal koşum olarak açıklanır. Yeni rapor mevcut deneyleri genişleterek yorumlar; çalıştırılmayan deneyler açıkça belirtilir.

![BERT için üç epoch boyunca eğitim kaybı ve doğrulama Macro F1](deliverables/tez_figures/ogrenme_egrileri.png)

Her dilde model seçimi doğrulama Macro-F1 ile yapıldı; seçilen epoch 3. Grafik üç ölçüm noktasını gösterir, daha uzun eğitimin davranışına ilişkin kanıt sağlamaz. [Sayısal epoch kayıtları](deliverables/tez_tables/epoch_metrics.csv).

![İki dilde bütün yöntemlerin negatif nötr ve pozitif sınıf F1 değerleri](deliverables/tez_figures/sinif_f1.png)

Sınıf F1 değerleri kesinlik ile duyarlılığın dengesini gösterir. Türkçe Qwen negatif ve pozitif sınıflarında daha yüksek duyarlılığa sahip olsa da nötr örneklerden gelen yanlış pozitifler bu sınıfların kesinliğini düşürür. [Bütün tez grafikleri](deliverables/tez_figures) · [Kaynakça kayıtları](thesis_references.py).

GitHub raporunda öğrenci numaraları gizlidir. Tam bilgileri içeren teslim sürümü çalışma bilgisayarındaki `teslim_ozel` klasöründe tutulur ve depoya eklenmez. Teslim ZIP'i GitHub'a yüklenmez.

Raporu korunan sonuçlardan yeniden üretmek için ayrı bir Python ortamında:

```powershell
python -m pip install -r requirements-report.txt
python 13_build_thesis_assets.py
python 14_write_thesis.py
```

Windows ve Microsoft Word varsa `tools/finalize_thesis_word.ps1` içindekiler alanlarını güncelleyip denetim PDF'i oluşturur. Alternatif olarak belgeyi Word'de açıp tüm alanları güncellemek için **Ctrl+A, F9** kullanılabilir. Bu komutlar eğitim veya yeni LLM çağrısı yapmaz.

## Gerçek deney sonuçları

![İki dilde VADER BERT ve Qwen için accuracy ve Macro-F1 karşılaştırması](deliverables/figures/comparison.png)

Her satır **3.000 test yorumu**, her gerçek sınıf **1.000 yorum** içerir. Aynı dilde bütün yöntemlere aynı test metinleri verilmiştir. Geçersiz çıktı sayısı altı koşumda da **0**'dır.

__RESULTS__

¹ Türkçe doğrudan VADER, **tanısal başlangıç deneyidir**. Standart İngilizce sözlüğün Türkçe üzerindeki davranışını gösterir; yerleşik Türkçe duygu desteği olarak sunulmaz.

**Grafik nasıl okunur?** Her iki ölçekte de yüksek değer daha iyidir. Accuracy tüm testte doğru tahmin oranını, Macro-F1 üç sınıfın F1 ortalamasını gösterir. Grafiklerde gösterilmeyen ya da çalıştırılmamış deneyler sıfır puanmış gibi eklenmemiştir.

**İngilizce bulgu:** BERT accuracy bakımından %69,00 ile önde; Qwen Macro-F1 bakımından 0,6867 ile çok az yüksek. İki yöntemin Macro-F1 farkı yaklaşık **0,0024**; istatistiksel anlamlılık testi yapılmadı. Tek bir metrik üzerinden kesin model üstünlüğü çıkarılmamalı.

**Türkçe bulgu:** BERT hem accuracy hem Macro-F1 bakımından en yüksek genel sonucu verdi. Qwen negatif ve pozitif sınıflarında daha az hata yaparken nötr sınıfta 569 hata yaptı. Dolayısıyla sınıf davranışlarını ayrıca incelemek gerekiyor.

## Sınıflara göre hatalar

![Her gerçek duygu sınıfında üç yöntemin yanlış tahmin sayıları](deliverables/figures/class_errors.png)

Her sütunun paydası **1.000**'dir. Düşük sütun daha az hata anlamına gelir. Hatalar gerçek sınıfa göre sayılır:

```text
Yanlış(c) = Gerçek etiketi c olan toplam yorum − doğru tahmin edilen c yorumları
```

Örneğin gerçek etiketi negatif olan bir yorum nötr tahmin edildiyse hata negatif sınıfa yazılır. Geçersiz veya başarısız bir model yanıtı da yanlış tahmindir; paydadan çıkarılmaz.

- İngilizce BERT, VADER'a göre negatif sınıf yanlışını **447'den 148'e** düşürdü.
- İngilizce Qwen'in nötr sınıfında **278**, BERT'in aynı sınıfında **497** yanlış tahmini var.
- Türkçe Qwen'in negatif ve pozitif sınıf yanlışları **106 ve 115**; nötr sınıf yanlışı **569**.
- Türkçe doğrudan VADER **3.000 yorumun 2.772'sini nötr** tahmin etti. Nötr sınıftaki yüksek recall tek başına başarı göstergesi değildir.

Sınıf başına destek, doğru, yanlış, hata oranı, precision, recall ve F1 değerleri [class_metrics.csv](deliverables/class_metrics.csv) dosyasında yer alır.

## Karışıklık matrisleri

### İngilizce

![İngilizce testte VADER BERT ve Qwen karışıklık matrisleri](deliverables/figures/confusion_en.png)

### Türkçe

![Türkçe testte doğrudan tanısal VADER BERT ve Qwen karışıklık matrisleri](deliverables/figures/confusion_tr.png)

**Satırlar gerçek sınıfı, sütunlar tahmini gösterir.** Köşegen doğru tahminlerdir; diğer hücreler hata yönleridir. Geçersiz çıktılar ayrı sütunda tutulur. Her satırın toplamı 1.000'dir.

Türkçe Qwen'de **nötr → negatif 319**, **nötr → pozitif 250** yorum görülür. Bu dağılım, nötr sınıf hatalarının tek yönde toplanmadığını gösterir. Türkçe BERT'te aynı iki yön **102 ve 138**'dir. Bütün yönler [error_directions.csv](deliverables/error_directions.csv) içinde saklanır.

## Veri ve deney tasarımı

| Dil | Kaynak | Alan | Eğitim | Doğrulama | Test |
|---|---|---|---:|---:|---:|
| İngilizce | TweetEval sentiment[^tweeteval] | Sosyal medya | 11.400 | 600 | 3.000 |
| Türkçe | TRSAv1[^trsa] | Ürün yorumları | 11.400 | 600 | 3.000 |

Her dilde her sınıftan eğitimde **3.800**, doğrulamada **200**, testte **1.000** yorum vardır. Kaynak ve temiz havuzların her sınıfı en az 1.000 yorum koşulunu karşılar. İngilizce resmi bölüm sınırları korunmuştur; Türkçe bölümler seed 42 ile sabitlenmiştir.

```mermaid
flowchart LR
  A["Sabit veri bölümleri"] --> TR["Eğitim 11400 / dil"]
  A --> VA["Doğrulama 600 / dil"]
  A --> TE["Test 3000 / dil · yalnızca metin ve ID"]
  TR --> B["BERT fine tuning"]
  VA -->|"Checkpoint seçimi"| B
  VA -->|"Zero-shot pilot"| L["Qwen 2.5 7B"]
  TE --> V["Orijinal VADER"]
  TE --> B
  TE --> L
  V --> E["ID ile ortak değerlendirme"]
  B --> E
  L --> E
  E --> R["Sınıf hataları · Accuracy · Macro-F1"]
```

Boş metin, tam tekrar, çelişkili etiket, bölüm kesişimi ve dosya hashleri denetlendi. Emoji, noktalama, olumsuzluk ve büyük harf korunur. BERT yalnızca eğitim verisiyle öğrenir; checkpoint doğrulama Macro-F1 ile seçilir. LLM pilotu da doğrulama verisindedir. Test etiketleri modele gönderilmez ve test sonuçlarıyla prompt seçilmez.

[Veri manifesti](data/manifest.json) kaynak commitlerini, sınıf sayılarını ve altı CSV'nin SHA256 değerlerini; [veri denetimi](audit/data_integrity.json) kontrol bulgularını içerir. Tahminler satır sırasıyla eşleştirilmez.

## Yöntemler ve kaynaklardan kısa alıntılar

### VADER

> “a lexicon and rule-based sentiment analysis tool”
>
> Kaynak: [VADER'ın özgün deposu](https://github.com/cjhutto/vaderSentiment).[^vader]

Bu kısa tanım sözlük ve kurallara dayanan yaklaşımı açıklar. Deneyde `vaderSentiment==3.3.2` ve standart compound eşikleri kullanıldı: ≤ −0,05 negatif; ≥ 0,05 pozitif; arası nötr. Türkçeye doğrudan uygulama tanısaldır. Ayrı çeviri + VADER çalıştırıcısı hazırdır; **çeviri deneyi yapılmadı**.

### BERT

> “mostly intended to be fine-tuned on a downstream task”
>
> Kaynak: [İngilizce BERT model kartı](https://huggingface.co/google-bert/bert-base-uncased).[^bert]

Ön eğitimli modelin hazır bir üç sınıflı duygu sınıflandırıcısı olduğu varsayılmadı. İngilizcede `google-bert/bert-base-uncased`, Türkçede `dbmdz/bert-base-turkish-cased` üzerine üç çıkışlı başlık eklenerek fine tuning yapıldı.[^berturk]

| Parametre | Uygulanan değer |
|---|---|
| Learning rate | `2e-5` |
| Batch size / gradient accumulation | `16 / 1` |
| En fazla token / epoch | `256 / 3` |
| Seed | `42` |
| Checkpoint seçimi | Doğrulama Macro-F1; iki dilde de epoch 3 |
| Doğrulama Macro-F1 | EN `0,7469` · TR `0,8511` |
| Donanım | NVIDIA GeForce RTX 3080 Ti · 12 GB |

### Büyük dil modeli

> “Multilingual support for over 29 languages”
>
> Kaynak: [Qwen2.5-7B-Instruct model kartı](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct).[^qwen]

İki dilde aynı **Qwen2.5 7B Instruct Q4_K_M** ağırlıkları ve aynı [zero-shot prompt](prompts/zero_shot_v1.txt) kullanıldı. Her dilde doğrulamadan 30 yorumla pilot yapıldı; prompt değiştirilmeden tam teste geçildi. Temperature 0, seed 42 ve en fazla üç deneme uygulandı. Ham yanıtlar, gecikmeler, token kullanımı ve yeniden denemeler [EN](runs/en_llm_test/records.jsonl) ve [TR](runs/tr_llm_test/records.jsonl) günlüklerinde saklanır. Başarısız yanıt nötre çevrilmez.

## Gerçek yorumlarla hata incelemesi

Aşağıdaki alıntılar değerlendirme verisindeki **gerçek metinlerdir**. Gerçek etiket kaynak veri setinden gelir; model tahmini korunmuştur. Açıklamalar olası yorumlardır, kesin hata nedeni veya yeniden etiketleme kararı değildir.

__CASES__

Bu beş örnek, olguları açıklamak amacıyla seçildi; kategori sıklıklarını temsil etmez. Ayrıca her dil ve yöntemde gerçek sınıf başına beş yanlış yorum seed 42 ile seçildi: toplam **90 örnek** [insan inceleme CSV'sinde](deliverables/error_review_sample.csv). İki grup üyesinin bağımsız inceleme alanları henüz doldurulmadı. Açıklamalı vakaların tam ID ve etiketleri [error_case_studies.csv](deliverables/error_case_studies.csv) içindedir.

## Sonuçları hangi sınırlar içinde okumalıyız

- **Alan farkı:** İngilizce sosyal medya, Türkçe ürün yorumu. Diller arasındaki fark yalnızca dilin etkisi değildir.
- **Eğitim farkı:** BERT etiketli eğitim verisi gördü; Qwen zero-shot koşulunda çalıştı.
- **Etiket sınırı:** Nötr, karışık duygu ve olası etiket gürültüsü değerlendirmeyi etkileyebilir; altın etiketler değiştirilmedi.
- **Tekrar sınırı:** Ana BERT deneyi tek seed içerir. Üç seed ve çeviri + VADER seçenekleri çalıştırılmadı.
- **Ön eğitim:** Açık veri ile ön eğitim verisi çakışması ve yakın tekrarlar tümüyle dışlanamaz.
- **Çalıştırıcı sürümü:** Türkçe LLM'de ilk 2.318 kayıt Ollama 0.40.15, kalan 682 kayıt 0.40.16 ile üretildi. Kesintiden sonra aynı ağırlık digest'i ve prompt korunarak devam edildi. Sürüm farkı tekrar üretilebilirlik sınırlılığıdır.
- **Süre:** BERT optimizasyon süresi indirme ve checkpoint yazmayı kapsamaz. Türkçe LLM'nin ilk oturumunun tam duvar süresi kaydedilemedi; bütün yorumların ölçülmüş gecikmeleri korundu.

## Dosyalarda ne var

| Yol | İçerik |
|---|---|
| [`data/`](data) | Sabit veri bölümleri, kaynak sürümleri ve manifest |
| [`results/`](results) | Korunan VADER metrikleri ve yanlış yorumları |
| [`runs/`](runs) | BERT ve LLM koşum ayarları, tahminler ve değerlendirmeler |
| [`deliverables/figures/`](deliverables/figures) | README'de gösterilen gerçek grafikler |
| [`deliverables/Proje_Raporu.docx`](deliverables/Proje_Raporu.docx) | Türkçe Word raporu |
| [`deliverables/Proje_Raporu_Tez.docx`](deliverables/Proje_Raporu_Tez.docx) | Tez düzeninde genişletilmiş akademik rapor |
| [`deliverables/tez_figures/`](deliverables/tez_figures) | Korunan deneylerden türetilen yedi tez grafiği |
| [`14_write_thesis.py`](14_write_thesis.py) | Akademik rapor oluşturucu; metin ve kaynaklar ayrı Python dosyalarında |
| [`deliverables/SUNUM_VE_KONUSMA_TASLAGI.md`](deliverables/SUNUM_VE_KONUSMA_TASLAGI.md) | Üç kişi için dokuz dakikalık akış ve konuşma metni |
| [`audit/`](audit) | Veri, model, test ve belge denetim kayıtları |
| [`GITHUB_ERISIM.md`](GITHUB_ERISIM.md) | Projeyi GitHub üzerinden indirme |

Teslim tarihi **25 Kasım 2026 Çarşamba ders saatidir**; grup tam **üç kişi**. İnsan hata incelemesi, video kaydı ve gerçek teslim grup tarafından tamamlanacaktır. **İmza karşılığı elden teslim ve e-posta gönderimi birlikte zorunludur.** Eklenti sınırına takılınırsa bütün materyallerin OneDrive bağlantısı e-postaya eklenir. GitHub paylaşımı bu teslimlerin yerine geçmez. Güncel eşleştirme: [ödev uygunluk kontrolü](deliverables/ODEV_UYGUNLUK_KONTROLU.md).

__GROUP__

## Kurulum ve yeniden üretme

Grafik ve tabloları incelemek için model çalıştırmanız gerekmez. Standart Python ile yazılım ve veri denetimlerini çalıştırabilirsiniz:

```powershell
git clone https://github.com/tubadeligoz/duygu-analizi-odev.git
cd duygu-analizi-odev
python -m unittest discover -s . -p "test_*.py" -v
python 00_audit.py
```

<details>
<summary><strong>Tam kurulum, BERT eğitimi, LLM pilotu ve tekrar üretme komutlarını aç</strong></summary>

__GUIDE_START__

__GUIDE__

__GUIDE_END__

</details>

## Kaynaklar

Kaynaklardan yapılan doğrudan alıntılar yukarıda kısa tutuldu ve özgün dillerinde verildi. Grafikler başka bir yayından alınmadı; bu projenin gerçek tahminlerinden üretildi. Kaynak kartlarına erişim tarihi **18 Kasım 2026**.

[^tweeteval]: Barbieri, F., Camacho-Collados, J., Espinosa-Anke, L. ve Neves, L. (2020). *TweetEval: Unified Benchmark and Comparative Evaluation for Tweet Classification*. [Özgün makale](https://aclanthology.org/2020.findings-emnlp.148/) · [Veri kartı](https://huggingface.co/datasets/cardiffnlp/tweet_eval).
[^trsa]: Aydoğan, M. ve Kocaman, V. *TRSAv1: A new benchmark dataset for classifying user reviews on Turkish e-commerce websites*. [DOI ve özgün yayın](https://doi.org/10.1177/01655515221074328) · [Veri kartı](https://huggingface.co/datasets/maydogan/Turkish_SentimentAnalysis_TRSAv1).
[^vader]: Hutto, C. J. ve Gilbert, E. (2014). *VADER: A Parsimonious Rule-based Model for Sentiment Analysis of Social Media Text*. [Özgün uygulama ve atıf bilgisi](https://github.com/cjhutto/vaderSentiment).
[^bert]: Devlin, J., Chang, M.-W., Lee, K. ve Toutanova, K. (2019). *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*. [Makale](https://aclanthology.org/N19-1423/) · [İngilizce model kartı](https://huggingface.co/google-bert/bert-base-uncased).
[^berturk]: dbmdz. *BERTurk cased model*. [Türkçe model kartı](https://huggingface.co/dbmdz/bert-base-turkish-cased).
[^qwen]: Qwen Team. *Qwen2.5-7B-Instruct*. [Model kartı](https://huggingface.co/Qwen/Qwen2.5-7B-Instruct) · [Ollama nicemleme bilgisi](https://ollama.com/library/qwen2.5:latest).

Uygulama API'ları: [Transformers sınıflandırma kılavuzu](https://huggingface.co/docs/transformers/en/tasks/sequence_classification) · [Ollama chat API](https://docs.ollama.com/api/chat). Kaynak sürümleri ve dosya hashleri bu depodaki manifest ve koşum kayıtlarında yer alır.
'''
    snippets = []
    label_tr = {"negative": "negatif", "neutral": "nötr", "positive": "pozitif"}
    for case in cases:
        text = "\n".join("> " + line for line in case["text"].splitlines())
        snippets.append(f"### {case['category']}\n\n{text}\n\n"
                        f"**{case['language'].upper()} · {case['method']}** — Kaynak etiket **{label_tr[case['label']]}**, "
                        f"tahmin **{label_tr[case['prediction']]}**.\n\n{case['interpretation']}\n")
    content = intro.replace("__RESULTS__", table).replace("__CASES__", "\n".join(snippets))
    group_text = ""
    if group:
        group_text = "## Grup ve ders\n\n**" + group["course"] + "**\n\nÖğretim elemanı: **" + group["instructor"] + "**\n\n"
        group_text += "| Grup üyesi | Ad Soyad |\n|---|---|\n"
        group_text += "\n".join(f"| {i} | {m['name']} |" for i, m in enumerate(group["members"], 1))
        group_text += "\n\nKapak bilgileri tamamlandı. Öğrenci numaraları GitHub kopyasında gizlidir; tam bilgiler özgün çalışma bilgisayarındaki yerel teslim raporunda bulunur. [Teslim kontrol listesi](deliverables/TESLIM_KONTROL_LISTESI.md).\n"
    content = content.replace("__GROUP__", group_text)
    content = content.replace("__GUIDE_START__", START).replace("__GUIDE_END__", END).replace("__GUIDE__", guide)
    (ROOT / "README.md").write_text(content, encoding="utf-8")
    print("Built README with 6 real figures, thesis report, 5 real error cases and linked references")


if __name__ == "__main__":
    main()
