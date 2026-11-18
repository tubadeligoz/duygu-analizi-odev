"""Build a Turkish Word report from verified metrics; use the bundled document Python."""
import argparse
import json
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt, RGBColor

from common import LABELS, read_csv
from experiment_utils import ROOT

TURKISH = {"negative": "Negatif", "neutral": "Nötr", "positive": "Pozitif"}


def number(value, decimals=4):
    return f"{value:.{decimals}f}".replace(".", ",")


def percent(value):
    return "%" + number(value * 100, 2)


def paragraph(doc, text, style=None):
    p = doc.add_paragraph(text, style)
    p.paragraph_format.space_after = Pt(7)
    return p


def heading(doc, text, level=1):
    return doc.add_heading(text, level)


def table(doc, headers, rows, widths=None, font=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    if widths:
        for column, width in zip(t.columns, widths):
            column.width = Cm(width)
    for cell, value in zip(t.rows[0].cells, headers):
        cell.text = str(value)
    for values in rows:
        cells = t.add_row().cells
        for cell, value in zip(cells, values):
            cell.text = str(value)
    for i, row in enumerate(t.rows):
        if i == 0:
            repeat = OxmlElement("w:tblHeader")
            row._tr.get_or_add_trPr().append(repeat)
        prevent = OxmlElement("w:cantSplit")
        row._tr.get_or_add_trPr().append(prevent)
        for j, cell in enumerate(row.cells):
            if widths:
                cell.width = Cm(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            props = cell._tc.get_or_add_tcPr()
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "E9EFF3" if i == 0 else ("F6F8FA" if i % 2 == 0 else "FFFFFF"))
            props.append(shade)
            borders = OxmlElement("w:tcBorders")
            for side in ("top", "left", "bottom", "right"):
                border = OxmlElement("w:" + side)
                for key, value in (("val", "single"), ("sz", "4"), ("color", "D9D9D9")):
                    border.set(qn("w:" + key), value)
                borders.append(border)
            props.append(borders)
            margins = OxmlElement("w:tcMar")
            for side, width in (("top", "75"), ("bottom", "75"), ("left", "90"), ("right", "90")):
                margin = OxmlElement("w:" + side)
                margin.set(qn("w:w"), width)
                margin.set(qn("w:type"), "dxa")
                margins.append(margin)
            props.append(margins)
            for p in cell.paragraphs:
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.line_spacing = 1.05
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j < 2 else WD_ALIGN_PARAGRAPH.CENTER
                for run in p.runs:
                    run.font.size = Pt(font)
                    run.font.bold = i == 0
                    run.font.color.rgb = RGBColor(0, 0, 0)
    paragraph(doc, "").paragraph_format.space_after = Pt(1)
    return t


def picture(doc, path, caption):
    doc.add_picture(str(path), width=Cm(17.2))
    # Real alt text, not merely a filename.
    shape = doc.inline_shapes[-1]
    shape._inline.docPr.set("descr", caption)
    p = paragraph(doc, caption)
    p.paragraph_format.space_after = Pt(9)
    for run in p.runs:
        run.font.size = Pt(9)


def new_page(doc, title):
    h = heading(doc, title)
    h.paragraph_format.page_break_before = True


def build(data, output, group=None, assets=None):
    assets = Path(assets or output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    integrity = json.loads((ROOT / "audit/data_integrity.json").read_text(encoding="utf-8"))
    runs = data["runs"]
    index = {(r["language"], r["method"]): r for r in runs}
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.top_margin, section.bottom_margin = Cm(1.9), Cm(1.8)
    section.left_margin = section.right_margin = Cm(1.9)
    for style_name in ("Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3"):
        style = doc.styles[style_name]
        style.font.name = "Arial"
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.font.size = Pt({"Title": 23, "Subtitle": 13, "Heading 1": 16, "Heading 2": 12}.get(style_name, 10.5))
        style.paragraph_format.line_spacing = 1.12
        if style_name.startswith("Heading"):
            style.paragraph_format.space_before = Pt(12)
            style.paragraph_format.space_after = Pt(7)
    doc.core_properties.title = "İngilizce ve Türkçe Metinlerde Duygu Analizi"
    doc.core_properties.subject = "VADER BERT ve Qwen yöntemlerinin tekrarlanabilir karşılaştırması"
    doc.core_properties.author = "; ".join(m["name"] for m in group["members"]) if group else ""
    paragraph(doc, "İngilizce ve Türkçe Metinlerde Duygu Analizi", "Title")
    paragraph(doc, "VADER BERT ve Qwen yöntemlerinin karşılaştırılması", "Subtitle")
    paragraph(doc, "Deney tarihi 18 Kasım 2026    Teslim tarihi 25 Kasım 2026")
    members = [[f"Üye {i+1}", m["name"], m["student_number"]] for i, m in enumerate(group["members"])] if group else [[f"Üye {i+1}", "Doldurulacak", "Doldurulacak"] for i in range(3)]
    table(doc, ["Grup üyesi", "Ad Soyad", "Öğrenci numarası"], members, [2.6, 8, 6.6])
    if group:
        paragraph(doc, "Ders " + group["course"])
        paragraph(doc, "Öğretim elemanı " + group["instructor"])
        if group["audience"] == "public":
            paragraph(doc, "GitHub kopyasında öğrenci numaraları gizlidir. Tam bilgiler yerel teslim sürümünde bulunur.")
    else:
        paragraph(doc, "Ders ve öğretim elemanı bilgileri grup tarafından eklenecektir.")
    heading(doc, "Özet")
    best = []
    for lang in ("en", "tr"):
        subset = [r for r in runs if r["language"] == lang]
        winner = max(subset, key=lambda r: r["metrics"]["macro_f1"])
        best.append(f"{lang.upper()} bölümünde en yüksek ölçülen Macro F1 {number(winner['metrics']['macro_f1'])} ile {winner['display_name']} yöntemine aittir")
    paragraph(doc, "Bu çalışma, İngilizce TweetEval sosyal medya metinleri ile Türkçe TRSAv1 ürün yorumlarında negatif, nötr ve pozitif duygu sınıflandırmasını inceler. Her dilde 11.400 eğitim, 600 doğrulama ve 3.000 test metni kullanılmıştır. Aynı dilde bütün yöntemler aynı 3.000 test ID’si üzerinde değerlendirilmiştir. " + ". ".join(best) + ".")
    paragraph(doc, "VADER sabit kurallarla, BERT yalnızca eğitim etiketleriyle fine tuning yapılarak, Qwen ise zero shot biçiminde uygulanır. Bu eğitim koşulları eşdeğer değildir. Türkçe doğrudan VADER bir tanısal başlangıç deneyidir. Alan ve etiketleme farkları nedeniyle diller arasındaki performans farkı dil etkisi olarak yorumlanamaz.")
    if data["unavailable"]:
        paragraph(doc, "Tamamlanmayan deneyler: " + ", ".join(r["language"].upper() + " " + r["method"] for r in data["unavailable"]) + ". Bu yöntemler için ölçüm yazılmamıştır.")
    heading(doc, "Araştırma sorusu")
    paragraph(doc, "Kural tabanlı, denetimli ve büyük dil modeli temelli yöntemler hangi gerçek duygu sınıflarında hata yapmaktadır? Accuracy yanında Macro F1 ve gerçek sınıf başına yanlış sayısı incelenir. Test sonuçları görüldükten sonra eşik, prompt veya hiperparametre seçilmemiştir.")

    new_page(doc, "Veri kaynakları ve bütünlük")
    paragraph(doc, "İngilizce veri CardiffNLP TweetEval veri setinin sentiment konfigürasyonundan, Türkçe veri TRSAv1 kaynağından alınmıştır [1, 2]. İngilizce resmi train validation test sınırları korunmuştur. Türkçe kaynak tek havuzdan sınıf bazında seed 42 ile bölünmüştür.")
    rows = []
    for lang in ("en", "tr"):
        spec = manifest["datasets"][lang]
        rows.append([lang.upper(), "/".join(str(spec["raw_class_counts"][c]) for c in LABELS),
                     "/".join(str(spec["clean_class_counts"][c]) for c in LABELS),
                     spec["audit"]["duplicate_rows_removed"], spec["audit"]["conflicting_rows_removed"]])
    table(doc, ["Dil", "Kaynak N / Ntr / P", "Temiz N / Ntr / P", "Tekrar", "Çelişki satırı"], rows, [1, 5.2, 5.2, 2.4, 3.4], 8.8)
    paragraph(doc, "N negatif, Ntr nötr, P pozitif sınıfını gösterir. Kaynak ve temiz havuz sayıları sabit manifestten alınmıştır. Ham kaynak bu devam çalışmasında yeniden indirilmemiştir. Çelişki sayısı benzersiz metin grubu değil çıkarılan satır sayısıdır.")
    table(doc, ["Bölüm", "Negatif", "Nötr", "Pozitif", "Toplam her dilde"],
          [["Eğitim", 3800, 3800, 3800, 11400], ["Doğrulama", 200, 200, 200, 600],
           ["Test", 1000, 1000, 1000, 3000]], [3.2, 3.2, 3.2, 3.2, 4.4])
    heading(doc, "Denetim bulguları", 2)
    paragraph(doc, "Altı bölüm dosyasının SHA256 değerleri manifestle aynıdır. 30.000 satırda boş metin, geçersiz etiket, tekrar ID, normalleştirilmiş tam metin tekrarı ve bölümler arası tam metin sızıntısı kontrolleri geçmiştir. Kaynaktaki çelişkili etiket gruplarının çıkarılan ID’leri seçili bölümlere dönmemiştir. Her kaynak sınıfı en az 1.000 örnek koşulunu karşılar.")
    paragraph(doc, "Temizleme Unicode NFC, HTML çözümü ve boşluk düzenlemesiyle sınırlıdır. Emoji, olumsuzluk, büyük harf ve noktalama korunur. İngilizce eğitim verisindeki sekiz metinde iç içe HTML entity kalmıştır; özgün bölüm ve hashleri korumak için yeniden çözüm uygulanmamıştır. Bütün yöntemler aynı saklanan metni alır.")
    paragraph(doc, "Yakın tekrarlar ile kullanıcı veya ürün düzeyindeki ortaklıklar bu kontrolle dışlanamaz. Etiketler kaynak etiketleridir; bütün metinler yeniden elle etiketlenmemiştir. TweetEval sosyal medya, TRSAv1 e ticaret alanındadır; nötr sınıfının kapsamı da kaynaklar arasında değişebilir.")
    heading(doc, "Sabit kaynak sürümleri", 2)
    for lang in ("en", "tr"):
        spec = manifest["datasets"][lang]
        paragraph(doc, f"{lang.upper()} {spec['repo']}\n{spec['revision']}")

    new_page(doc, "Yöntemler ve çalışma koşulları")
    heading(doc, "VADER", 2)
    paragraph(doc, "Orijinal vaderSentiment 3.3.2 kullanılmıştır [3]. Compound değeri en fazla −0,05 ise negatif, en az 0,05 ise pozitif, arada ise nötrdür. Türkçe doğrudan uygulama dil uyumsuzluğunu gösteren tanısal başlangıç deneyidir; yerleşik Türkçe desteği olarak sunulmaz. Çeviri ve VADER hattı ayrı bir isteğe bağlı çalıştırıcı olarak hazırlanmıştır; bu rapordaki temel altı sonuca dahil değildir.")
    heading(doc, "BERT", 2)
    paragraph(doc, "İngilizcede google bert base uncased, Türkçede dbmdz bert base turkish cased modellerine üç çıkışlı sınıflandırma başlığı eklenmiştir [4, 5]. Bütün model parametreleri eğitim verisinde güncellenir. Etiket eşlemesi negative 0, neutral 1, positive 2 olarak sabittir. Checkpoint yalnızca doğrulama Macro F1 değeriyle seçilir; eşitlikte erken epoch korunur.")
    table(doc, ["Ayar", "Uygulanan değer"], [["Öğrenme oranı", "0,00002"], ["Batch ve accumulation", "16 ve 1   Etkin batch 16"],
          ["Uzunluk ve epoch", "256 token   En fazla 3 epoch"], ["Seed", "42"], ["Optimizer ve scheduler", "AdamW   weight decay 0,01   doğrusal azalma"],
          ["Duyarlık ve clipping", "FP16 autocast   gradient norm üst sınırı 1,0"]], [5, 12.2])
    for lang in ("en", "tr"):
        r = index.get((lang, "bert"))
        if r:
            m = r["metadata"]
            paragraph(doc, f"{lang.upper()} seçilen epoch {m['selection']['epoch']}; doğrulama Macro F1 {number(m['selection']['validation_macro_f1'])}. Model ve tokenizer commit {m['config']['model_revision']}. Optimizasyon süresi {number(m['training']['training_seconds'], 2)} saniye; test çıkarımı {number(m['inference_seconds'], 2)} saniye. Testte kesilen metin oranı {percent(m['test_truncation']['truncation_rate'])}.")
    heading(doc, "Büyük dil modeli", 2)
    paragraph(doc, "Her iki dilde aynı yerel Qwen2.5 7B Instruct Q4_K_M modeli kullanılır [6]. Model donanımda önceden bulunduğu ve belleğe sığdığı için testten önce seçilmiştir. Aynı İngilizce sınıf tanımları ve prompt iki dilde korunmuştur. Her dilde doğrulama bölümünden sınıf başına 10 metinlik pilot yapılır; temel deney zero shot’tır. İnceleme metnindeki talimatlar veri olarak sınırlandırılır. Model girdisinde altın etiket, puan veya sınıf bilgisi bulunmaz.")
    paragraph(doc, "Temperature 0, seed 42, bağlam 4.096 token, en fazla 16 çıktı tokenı, 90 saniye timeout ve en fazla 3 deneme uygulanır. Yalnızca negative, neutral ve positive kabul edilir. Başarısız yanıtlar __invalid__ olarak saklanır ve paydada kalır. ID, ham yanıt, bütün denemeler, gecikme ve token sayıları günlükte tutulur. Yerel koşumda sağlayıcı API ücreti sıfırdır; enerji ve donanım maliyeti ölçülmemiştir.")
    paragraph(doc, "Yeni BERT ve LLM deneyleri Windows üzerinde 12 GB NVIDIA GeForce RTX 3080 Ti ile yürütülmüştür. BERT ortamı Python 3.11.1, PyTorch 2.5.1 cu121 ve Transformers 5.6.1’dir. Başlangıç VADER sonuçları farklı koşumdan korunmuştur; onun donanımı kaydedilmemiştir. Süreler bir donanım hız yarışı olarak yorumlanmamalıdır.")

    add_architecture_page(doc)
    # Remaining report pages use the same verified results and shared figure assets.
    add_results_pages(doc, data, index, assets)
    for root in (doc.styles.element, doc._element):
        for border in root.xpath(".//w:pBdr"):
            border.getparent().remove(border)
    doc.save(output / "Proje_Raporu.docx")


def add_architecture_page(doc):
    new_page(doc, "Model mimarileri ve doğrulama pilotları")
    paragraph(doc, "BERT model yapıları kaydedilmiş best/config.json dosyalarından alınmıştır. Bu mimari özellikler kullanılan eğitim ayarlarından ayrıdır; örneğin modelin konum kapasitesi 512 olsa da deneyde en fazla 256 token kullanılmıştır [4, 5].")
    configs = {lang: json.loads((ROOT / "runs" / f"{lang}_bert_seed42" / "best/config.json").read_text()) for lang in ("en", "tr")}
    rows = []
    for title, key in (("Encoder katmanı", "num_hidden_layers"), ("Dikkat başlığı", "num_attention_heads"),
                       ("Gizli boyut", "hidden_size"), ("Ara katman boyutu", "intermediate_size"),
                       ("Sözlük büyüklüğü", "vocab_size"), ("Konum kapasitesi", "max_position_embeddings")):
        rows.append([title, configs["en"][key], configs["tr"][key]])
    rows.append(["Çıktı sınıfı", 3, 3])
    table(doc, ["Mimari özelliği", "İngilizce BERT", "Türkçe BERTurk"], rows, [7.2, 5, 5])
    paragraph(doc, "İki model de çift yönlü encoder mimarisine sahiptir. BertForSequenceClassification metin temsilini üç sınıflı sınıflandırma başlığına aktarır. Tek etiketli sınıflandırmada çapraz entropi kaybı kullanılır. Yeni başlıkla birlikte encoder parametreleri de fine tuning sırasında güncellenmiştir.")
    heading(doc, "Qwen yapısı ve yerel çıkarım", 2)
    paragraph(doc, "Qwen2.5 7B Instruct, instruction tuning uygulanmış bir decoder Transformer modelidir. Kaynak model kartında 28 katman, 28 sorgu başlığı ve 4 anahtar değer başlığı, RoPE konum temsili ve SwiGLU etkinleştirmesi belirtilir [6]. Bu projede kullanılan yerel ağırlık sürümü Q4_K_M nicemlemesine sahiptir. Modelin tam mimari kapasitesi ile deneyde seçilen 4.096 token bağlam sınırı aynı kavram değildir.")
    paragraph(doc, "LLM için eğitim bölümünde yeniden öğrenme yapılmadı. Her yorum bağımsız zero shot isteğidir. Aynı prompt ve sınıf tanımları korunmuş, test yorumlarının etiketleri ve kaynak puanları isteklerden çıkarılmıştır.")
    heading(doc, "Doğrulama pilotunun gerçek ölçümleri", 2)
    rows = []
    for lang in ("en", "tr"):
        m = json.loads((ROOT / "runs" / f"{lang}_llm_pilot" / "evaluation/metrics.json").read_text())
        rows.append([lang.upper(), m["n"], m["correct"], percent(m["accuracy"]), number(m["macro_f1"]), m["invalid_predictions"]])
    table(doc, ["Dil", "n", "Doğru", "Accuracy", "Macro F1", "Geçersiz"], rows, [1.5, 2, 2.5, 3.5, 4, 3.7])
    paragraph(doc, "Her pilotta doğrulama bölümünden sınıf başına 10 metin kullanılmıştır. Pilotlar çıktı sözleşmesini ve koşumu doğrulamak içindir; küçük pilot örneklemi nihai test sonucu olarak sunulmaz. Pilot sonrasında prompt değiştirilmeden sabit testlere geçilmiştir.")


def add_results_pages(doc, data, index, output):
    runs = data["runs"]
    new_page(doc, "Ortak test sonuçları")
    paragraph(doc, "Her satırda 3.000 test metni, her gerçek sınıfta 1.000 yorum vardır. Tahminler satır sırasıyla değil benzersiz ID ile eşleştirilmiştir. Eksik, fazla veya tekrar ID değerlendirmeyi durdurur. Geçersiz yanıtlar başarısız tahmin sayılır. Macro F1 üç gerçek sınıfın F1 değerlerinin aritmetik ortalamasıdır.")
    rows = []
    for r in runs:
        rows.append([r["language"].upper(), r["display_name"], *[c["incorrect"] for c in r["classes"]],
                     percent(r["metrics"]["accuracy"]), number(r["metrics"]["macro_f1"]), r["metrics"]["invalid_predictions"]])
    table(doc, ["Dil", "Yöntem", "Neg yanlış", "Nötr yanlış", "Poz yanlış", "Accuracy", "Macro F1", "Geçersiz"],
          rows, [0.9, 3.2, 2.1, 2.1, 2.1, 2.4, 2.4, 2.0], 8.2)
    picture(doc, output / "figures/comparison.png", "Şekil 1 Aynı testler üzerinde ölçülen accuracy ve Macro F1 değerleri")
    for lang in ("en", "tr"):
        subset = [r for r in runs if r["language"] == lang]
        best = max(subset, key=lambda r: r["metrics"]["macro_f1"])
        paragraph(doc, f"{lang.upper()} verisinde {best['display_name']} ölçülen en yüksek Macro F1 değerini vermiştir: {number(best['metrics']['macro_f1'])}. Bu bulgu, dengeli ve sabit alt kümeye aittir; genel model üstünlüğü veya dil etkisi hakkında tek başına sonuç vermez.")
    heading(doc, "Yanlış sayısının tanımı", 2)
    paragraph(doc, "Yanlış c = gerçek etiketi c olan toplam örnek − doğru tahmin edilen c örnekleri. Dolayısıyla negatif bir metnin nötr tahmini negatif sınıfın yanlış sayısına eklenir. Precision tahmini c olan örnekler içindeki doğruluğu, recall gerçek c örneklerinin bulunma oranını gösterir. Geçersiz çıktı recall ve accuracy paydasından çıkarılmaz.")

    new_page(doc, "Sınıf bazında değerlendirme")
    rows = []
    for r in runs:
        for c in r["classes"]:
            rows.append([r["language"].upper() + " " + r["display_name"], TURKISH[c["class"]], c["support"], c["correct"],
                         c["incorrect"], percent(c["error_rate"]), number(c["precision"], 3), number(c["recall"], 3), number(c["f1"], 3)])
    table(doc, ["Dil ve yöntem", "Sınıf", "n", "Doğru", "Yanlış", "Hata", "Prec", "Recall", "F1"], rows,
          [3.6, 2.0, 1.1, 1.3, 1.3, 1.9, 2, 2, 2], 8)
    picture(doc, output / "figures/class_errors.png", "Şekil 2 Gerçek sınıf başına yanlış sayıları   Her sütunun paydası 1.000")
    paragraph(doc, "Tam precision recall F1 ve false positive değerleri class_metrics.csv dosyasındadır. Genel accuracy yüksek olsa bile nötr sınıfın F1 değeri veya bir sınıfın hata oranı karar vermede farklı bir tablo gösterebilir.")

    new_page(doc, "Karışıklık matrisleri ve hata yönleri")
    picture(doc, output / "figures/confusion_en.png", "Şekil 3 İngilizce test   Satırlar gerçek sınıf sütunlar tahmin edilen sınıf")
    picture(doc, output / "figures/confusion_tr.png", "Şekil 4 Türkçe test   Geçersiz yanıtlar ayrı sütunda tutulur")
    paragraph(doc, "Türkçe orijinal VADER 3.000 yorumun 2.772’sini nötr tahmin etmiştir. Nötr sınıftaki yüksek recall, negatif ve pozitif metinlerin nötre yığılmasıyla birlikte değerlendirilmelidir. Bu, Türkçe duygu desteği kanıtı değildir.")
    for lang in ("en", "tr"):
        for r in (r for r in runs if r["language"] == lang):
            directions = [(r["matrix"][a][b], a, b) for a in LABELS for b in LABELS if a != b]
            count, a, b = max(directions)
            paragraph(doc, f"{lang.upper()} {r['display_name']} en sık hata yönü {TURKISH[a]} → {TURKISH[b]}: {count} yorum.")

    new_page(doc, "Gerçek örneklerle hata incelemesi")
    paragraph(doc, "Her dil ve yöntem için gerçek sınıf başına beş yanlış örnek seed 42 ile seçilerek error_review_sample.csv dosyasına yazılmıştır. Aşağıdaki beş vaka, dilsel olguları açıklayan amaçlı örnek seçimidir; hata kategorilerinin sıklığını temsil etmez. Açıklamalar yorumsaldır. İki grup üyesinin bağımsız değerlendirmesi henüz yapılmış sayılmaz. Altın etiketler değiştirilmemiştir.")
    cases = read_csv(output / "error_case_studies.csv") if (output / "error_case_studies.csv").exists() else []
    for case in cases:
        heading(doc, case["category"], 2)
        paragraph(doc, f"{case['language'].upper()} {case['method']}   Gerçek {case['label']}   Tahmin {case['prediction']}")
        p = paragraph(doc, "ID " + case["id"])
        for run in p.runs:
            run.font.size = Pt(8)
        paragraph(doc, "“" + case["text"] + "”")
        paragraph(doc, case["interpretation"])
    if not cases:
        paragraph(doc, "Vaka seçimi henüz tamamlanmadı. Rastgele inceleme örnekleri CSV dosyasında saklanmıştır.")

    new_page(doc, "Tartışma ve tekrarlanabilirlik")
    heading(doc, "Çalışmanın sınırlılıkları", 2)
    limitations = [
        "İngilizce sosyal medya ile Türkçe ürün yorumları farklı alanlardır. Diller arası farklar, alan ve etiketleme farklarıyla iç içedir.",
        "BERT etiketli eğitim verisi görmüştür; Qwen zero shot’tır. Sonuçlar eğitim bütçesi eşitlenmiş bir karşılaştırma değildir.",
        "Nötr sınıf ve karışık duygu sınırı kaynaklar arasında değişebilir. Olası etiket gürültüsü tek bir metin üzerinden kesinleştirilemez.",
        "Ön eğitim verilerinin açık veri setleriyle çakışmadığı garanti edilemez. Tam metin denetimi yakın tekrar veya aynı ürün ve kullanıcı sızıntısını dışlamaz.",
        "Ana BERT deneyi tek seed ile yapılmıştır. Üç seed seçeneği kodda desteklenir; bu tekrarlar çalıştırılmış gibi sunulmamıştır. GPU çekirdekleri ve yerel üretimde bit düzeyinde tekrar garantisi yoktur.",
        "Türkçe doğrudan VADER yalnızca tanısaldır. İsteğe bağlı çeviri hattı çalıştırılırsa çeviri hatası ve kesilme ayrıca değerlendirilmelidir.",
        "Test yorumlarındaki talimatların model tarafından tamamen etkisiz kalacağı garanti edilemez. Prompt veri sınırını açıklar; ham yanıtlar denetim için saklanır."
    ]
    for r in (r for r in runs if r["method"] == "llm"):
        versions = r["metadata"].get("runtime_version_record_counts", {})
        if len(versions) > 1:
            details = "; ".join(f"Ollama {v} ile {n} kayıt" for v, n in versions.items())
            limitations.append(f"{r['language'].upper()} LLM koşumu kesintiden sonra aynı ağırlık digest ve prompt ile sürdürülmüştür. {details}. Çalıştırıcı sürümü farkı sayısal tekrar üretilebilirlik için bir sınırlılıktır.")
    for text in limitations:
        paragraph(doc, text)
    heading(doc, "Tekrar üretme ve süreler", 2)
    paragraph(doc, "README komutları kurulumu, veri denetimini, eğitim ve pilot sırasını açıklar. data/manifest.json altı bölümün tam SHA256 değerlerini içerir. runs altındaki config, environment, history ve selection dosyaları model sürümleriyle parametreleri saklar. Her yöntemin yanlış yorumları evaluation/misclassified.csv içindedir. Bütün rapor sayıları 07_build_results.py tarafından özgün değerlendiriciyle tekrar hesaplanır.")
    for lang in ("en", "tr"):
        r = index.get((lang, "llm"))
        if r:
            m = r["metadata"]
            paragraph(doc, f"{lang.upper()} LLM son oturum duvar süresi {number(m['current_session_wall_seconds'], 2)} saniye; bütün yorumların istek gecikmeleri toplamı {number(m['summed_request_seconds'], 2)} saniye; giriş {m['input_tokens']} ve çıkış {m['output_tokens']} token. Paralel istek sayısı {m['workers']}. Geçersiz çıktı {m['invalid_predictions']}.")
    paragraph(doc, "BERT optimizasyon süreleri model indirme, veri kodlama ve checkpoint yazmayı kapsamaz. Türkçe LLM ilk oturumunun tam duvar süresi kesinti nedeniyle kaydedilememiştir; bütün yorumların ölçülmüş gecikmeleri korunmuştur. LLM testleri, modelin pilotta yüklendiği koşullarda başlamıştır.")
    heading(doc, "Sonuç", 2)
    paragraph(doc, "Bu ölçümler, yöntemlerin aynı sabit testlerde hangi sınıflara hata yaptığını karşılaştırmaya olanak verir. Türkçe doğrudan VADER’ın nötre yığılması kullanım koşullarının açıkça belirtilmesini gerektirir. Uygulama kararı yalnızca accuracy ile verilmemeli; nötr sınırı, sınıf bazlı hata, denetimli eğitim ihtiyacı ve çalışma süresi birlikte ele alınmalıdır.")

    new_page(doc, "Kaynakça ve deney eki")
    sources = [
        "[1] Barbieri F ve diğerleri 2020. TweetEval Unified Benchmark and Comparative Evaluation for Tweet Classification. https://aclanthology.org/2020.findings-emnlp.148/  Veri kartı https://huggingface.co/datasets/cardiffnlp/tweet_eval",
        "[2] Aydoğan M ve Kocaman V. TRSAv1 A new benchmark dataset for classifying user reviews on Turkish e commerce websites. https://doi.org/10.1177/01655515221074328  Veri kartı https://huggingface.co/datasets/maydogan/Turkish_SentimentAnalysis_TRSAv1",
        "[3] Hutto CJ ve Gilbert E 2014. VADER A Parsimonious Rule based Model for Sentiment Analysis of Social Media Text. https://github.com/cjhutto/vaderSentiment",
        "[4] Devlin J ve diğerleri 2019. BERT Pre training of Deep Bidirectional Transformers for Language Understanding. https://aclanthology.org/N19-1423/  Model kartı https://huggingface.co/google-bert/bert-base-uncased",
        "[5] dbmdz. BERTurk cased Turkish BERT model card. https://huggingface.co/dbmdz/bert-base-turkish-cased",
        "[6] Qwen Team. Qwen2.5 7B Instruct model card. https://huggingface.co/Qwen/Qwen2.5-7B-Instruct  Yerel sürüm https://ollama.com/library/qwen2.5:latest",
        "[7] Hugging Face. Transformers sequence classification API. https://huggingface.co/docs/transformers/en/tasks/sequence_classification",
        "[8] Ollama. Generate a chat message API. https://docs.ollama.com/api/chat"
    ]
    for text in sources:
        p = paragraph(doc, text)
        for run in p.runs:
            run.font.size = Pt(9)
    paragraph(doc, "Model ve veri kartlarının erişim tarihi 18 Kasım 2026’dır. Kesin deney commit ve model digest değerleri koşum dosyalarında tutulur.")
    llm = index.get(("en", "llm")) or index.get(("tr", "llm"))
    if llm:
        identity = llm["metadata"]["model_identity"]
        paragraph(doc, "Yerel LLM digest " + identity["digest"])
        paragraph(doc, "Ollama sürümü " + identity.get("ollama_version", "kaydedilmedi"))
    heading(doc, "Sabit zero shot prompt", 2)
    p = paragraph(doc, (ROOT / "prompts/zero_shot_v1.txt").read_text(encoding="utf-8"))
    for run in p.runs:
        run.font.name = "Consolas"
        run.font.size = Pt(8.5)
    paragraph(doc, "Kullanıcı mesajı yalnızca review alanında metni taşıyan JSON nesnesidir. Tam prompt hashleri pilot ve test koşumlarında karşılaştırılır. Bağımsız insan incelemesi, video kaydı ve gerçek teslim grup tarafından tamamlanacaktır. Teslim, 25 Kasım ders saatinde imza karşılığı elden ve e posta yoluyla birlikte yapılmalıdır. Eklenti boyutu aşılırsa bütün materyallerin OneDrive bağlantısı e postaya eklenmelidir.")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", default="deliverables")
    p.add_argument("--data-dir", help="Shared report data and figure directory; defaults to --output")
    p.add_argument("--group-info", default="configs/group_members.public.json")
    args = p.parse_args()
    output = Path(args.output)
    assets = Path(args.data_dir) if args.data_dir else output
    data = json.loads((assets / "report_data.json").read_text(encoding="utf-8"))
    group_path = Path(args.group_info)
    group = json.loads(group_path.read_text(encoding="utf-8")) if group_path.exists() else None
    if group:
        members = group.get("members", [])
        if len(members) != 3 or len({m["name"] for m in members}) != 3:
            p.error("Group must contain exactly three distinct members")
        if group.get("audience") not in ("public", "submission"):
            p.error("Group audience must be public or submission")
        if group["audience"] == "submission" and any(not str(m["student_number"]).isdigit() for m in members):
            p.error("Submission cover needs the real student numbers")
    build(data, output, group, assets)
    print("Created", output / "Proje_Raporu.docx")


if __name__ == "__main__":
    main()
