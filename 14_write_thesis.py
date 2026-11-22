"""Build public/private thesis-style Word reports without changing experiments.

Run with the bundled Codex document Python. Fields are finalized and rendered
with tools/finalize_thesis_word.ps1 on Windows with Microsoft Word installed.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re

from docx import Document
from docx.enum.section import WD_SECTION_START
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from common import LABELS, read_csv
from experiment_utils import ROOT, load_script, sha256, utc_now
from thesis_content import ABSTRACT_EN, ABSTRACT_TR, CHAPTERS
from thesis_references import REFERENCES, INDEX, formatted

LANG = {"en": "EN", "tr": "TR"}
LABEL = dict(zip(LABELS, ["Negatif", "Nötr", "Pozitif"]))


def num(value, n=4):
    return f"{value:.{n}f}".replace(".", ",")


def pct(value):
    return "%" + num(value * 100, 2)


def field(paragraph, instruction, placeholder=""):
    r = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    code = OxmlElement("w:instrText")
    code.set(qn("xml:space"), "preserve")
    code.text = " " + instruction + " "
    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")
    text = OxmlElement("w:t")
    text.text = placeholder
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    for element in (begin, code, separate, text, end):
        r._r.append(element)


def hyperlink(paragraph, label, url):
    rid = paragraph.part.relate_to(url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink", is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), rid)
    r = OxmlElement("w:r")
    props = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "000000")
    props.append(color)
    under = OxmlElement("w:u")
    under.set(qn("w:val"), "single")
    props.append(under)
    r.append(props)
    t = OxmlElement("w:t")
    t.text = label
    r.append(t)
    link.append(r)
    paragraph._p.append(link)


def para(doc, text="", style=None, keep=False):
    p = doc.add_paragraph(text, style)
    if keep:
        p.paragraph_format.keep_with_next = True
    return p


def numbering(doc):
    root = doc.part.numbering_part.element
    existing = [int(x.get(qn("w:abstractNumId"))) for x in root.findall(qn("w:abstractNum"))]
    abstract_id = max(existing, default=0) + 1
    abstract = OxmlElement("w:abstractNum")
    abstract.set(qn("w:abstractNumId"), str(abstract_id))
    kind = OxmlElement("w:multiLevelType")
    kind.set(qn("w:val"), "multilevel")
    abstract.append(kind)
    for i in range(3):
        level = OxmlElement("w:lvl")
        level.set(qn("w:ilvl"), str(i))
        for tag, val in [("start", "1"), ("numFmt", "decimal"),
                         ("lvlText", ".".join("%" + str(j+1) for j in range(i+1))),
                         ("lvlJc", "left"), ("suff", "space")]:
            node = OxmlElement("w:" + tag)
            node.set(qn("w:val"), val)
            level.append(node)
        abstract.append(level)
    root.append(abstract)
    nums = [int(x.get(qn("w:numId"))) for x in root.findall(qn("w:num"))]
    number_id = max(nums, default=0) + 1
    node = OxmlElement("w:num")
    node.set(qn("w:numId"), str(number_id))
    ref = OxmlElement("w:abstractNumId")
    ref.set(qn("w:val"), str(abstract_id))
    node.append(ref)
    root.append(node)
    return number_id


def heading(doc, text, level=1, number_id=None):
    p = doc.add_heading(text, level)
    if number_id is not None:
        props = p._p.get_or_add_pPr()
        np = OxmlElement("w:numPr")
        ilvl = OxmlElement("w:ilvl")
        ilvl.set(qn("w:val"), str(level-1))
        ni = OxmlElement("w:numId")
        ni.set(qn("w:val"), str(number_id))
        np.append(ilvl)
        np.append(ni)
        props.append(np)
    return p


def front_title(doc, text, page=True):
    p = para(doc, text, "Front Heading")
    p.paragraph_format.page_break_before = page
    return p


def set_page_numbers(section, fmt, start=1):
    pg = section._sectPr.find(qn("w:pgNumType"))
    if pg is None:
        pg = OxmlElement("w:pgNumType")
        section._sectPr.append(pg)
    pg.set(qn("w:fmt"), fmt)
    pg.set(qn("w:start"), str(start))
    section.footer.is_linked_to_previous = False
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1
    field(p, "PAGE")
    for r in p.runs:
        r.font.size = Pt(10)


def setup(doc):
    section = doc.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    section.left_margin, section.right_margin = Cm(3), Cm(2.5)
    section.top_margin, section.bottom_margin = Cm(2.5), Cm(2.5)
    section.header_distance, section.footer_distance = Cm(1.2), Cm(1.2)
    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption"]:
        s = doc.styles[name]
        s.font.name = "Times New Roman"
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.font.size = Pt(12)
        s.paragraph_format.first_line_indent = Cm(0)
    normal = doc.styles["Normal"]
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.first_line_indent = Cm(1.0)
    normal.paragraph_format.widow_control = True
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    for name, size in [("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 12)]:
        s = doc.styles[name]
        s.font.size = Pt(size)
        s.font.bold = True
        s.paragraph_format.space_before = Pt(14)
        s.paragraph_format.space_after = Pt(8)
        s.paragraph_format.line_spacing = 1.15
        s.paragraph_format.keep_with_next = True
        s.paragraph_format.keep_together = True
        if name == "Heading 1":
            s.paragraph_format.page_break_before = True
    doc.styles["Title"].font.size = Pt(20)
    doc.styles["Title"].font.bold = True
    doc.styles["Title"].paragraph_format.line_spacing = 1.25
    doc.styles["Subtitle"].font.size = Pt(14)
    for name, size in [("Front Heading", 14), ("Figure Caption", 10.5),
                       ("Table Caption", 10.5), ("Reference", 10.5), ("Source Note", 10),
                       ("Case Quote", 11), ("Code Block", 9)]:
        s = doc.styles.add_style(name, 1)
        s.base_style = doc.styles["Normal"]
        s.font.name = "Times New Roman"
        s.font.size = Pt(size)
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.paragraph_format.first_line_indent = Cm(0)
        s.paragraph_format.line_spacing = 1.1
        s.paragraph_format.space_after = Pt(7)
        s.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
        if name == "Front Heading":
            s.font.bold = True
            s.paragraph_format.keep_with_next = True
        if name.endswith("Caption"):
            s.font.bold = True
            s.paragraph_format.keep_with_next = name == "Table Caption"
        if name == "Reference":
            s.paragraph_format.left_indent = Cm(.8)
            s.paragraph_format.first_line_indent = Cm(-.8)
            s.paragraph_format.keep_together = True
            s.paragraph_format.space_after = Pt(4)
        if name == "Case Quote":
            s.font.italic = True
            s.paragraph_format.left_indent = Cm(.6)
            s.paragraph_format.right_indent = Cm(.3)
            s.paragraph_format.line_spacing = 1.25
        if name == "Code Block":
            s.font.name = "Consolas"
            s.paragraph_format.line_spacing = 1
    for name in ["TOC 1", "TOC 2", "TOC 3"]:
        if name not in doc.styles:
            doc.styles.add_style(name, 1)
        s = doc.styles[name]
        s.font.name = "Times New Roman"
        s.font.size = Pt(11)
        s.font.color.rgb = RGBColor(0, 0, 0)
        s.paragraph_format.first_line_indent = Cm(0)
        s.paragraph_format.line_spacing = 1.05
        s.paragraph_format.space_after = Pt(5)
        s.paragraph_format.left_indent = Cm(.6 if name == "TOC 2" else 0)
    # Turkish spell-check language and no theme accents or title rules.
    for s in doc.styles:
        if s.type == 1:
            for el in list(s.element.iter(qn("w:pBdr"))):
                el.getparent().remove(el)
            rpr = s.element.find(qn("w:rPr"))
            if rpr is not None:
                for fonts in rpr.findall(qn("w:rFonts")):
                    for attr in list(fonts.attrib):
                        if attr.endswith("Theme"):
                            del fonts.attrib[attr]
                for el in rpr.findall(qn("w:color")):
                    for a in list(el.attrib):
                        if a != qn("w:val"):
                            del el.attrib[a]
    lang = OxmlElement("w:lang")
    lang.set(qn("w:val"), "tr-TR")
    doc.styles["Normal"].element.get_or_add_rPr().append(lang)
    update = OxmlElement("w:updateFields")
    update.set(qn("w:val"), "true")
    doc.settings.element.append(update)


def table(doc, title, headers, rows, widths, font=10):
    para(doc, title, "Table Caption", keep=True)
    t = doc.add_table(rows=1, cols=len(headers))
    t.autofit = False
    for col, width in zip(t.columns, widths):
        col.width = Cm(width)
    for cell, value in zip(t.rows[0].cells, headers):
        cell.text = str(value)
    for values in rows:
        for cell, value in zip(t.add_row().cells, values):
            cell.text = str(value)
    for i, row in enumerate(t.rows):
        props = row._tr.get_or_add_trPr()
        if i == 0:
            props.append(OxmlElement("w:tblHeader"))
        props.append(OxmlElement("w:cantSplit"))
        for j, cell in enumerate(row.cells):
            cell.width = Cm(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            pr = cell._tc.get_or_add_tcPr()
            shade = OxmlElement("w:shd")
            shade.set(qn("w:fill"), "E9E9E9" if i == 0 else "FFFFFF")
            pr.append(shade)
            border = OxmlElement("w:tcBorders")
            for side in ["top", "left", "bottom", "right"]:
                e = OxmlElement("w:" + side)
                for k, v in [("val", "single"), ("sz", "4"), ("color", "D9D9D9")]:
                    e.set(qn("w:"+k), v)
                border.append(e)
            pr.append(border)
            margins = OxmlElement("w:tcMar")
            for side, val in [("top", 85), ("bottom", 85), ("left", 85), ("right", 85)]:
                e = OxmlElement("w:"+side)
                e.set(qn("w:w"), str(val))
                e.set(qn("w:type"), "dxa")
                margins.append(e)
            pr.append(margins)
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent = Cm(0)
                p.paragraph_format.line_spacing = 1.05
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.space_before = Pt(0)
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT if j < 2 else WD_ALIGN_PARAGRAPH.CENTER
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(font)
                    r.font.bold = i == 0
    spacer = para(doc, "")
    spacer.paragraph_format.space_after = Pt(0)
    spacer.paragraph_format.line_spacing = .4
    return t


def tables(runs, manifest):
    rows = []
    for lang in ["en", "tr"]:
        m = manifest["datasets"][lang]
        for cls in LABELS:
            rows.append([lang.upper(), LABEL[cls], f"{m['raw_class_counts'][cls]:,}".replace(",", "."),
                         f"{m['clean_class_counts'][cls]:,}".replace(",", ".")])
    d = {"source_counts": ("Tablo 1 Kaynak ve temiz havuzların sınıf büyüklükleri",
                           ["Dil", "Sınıf", "Kaynak", "Temiz havuz"], rows, [1.3, 4.6, 4.8, 4.8])}
    d["splits"] = ("Tablo 2 Her dil için sabitlenmiş veri bölümleri",
                   ["Bölüm", "Negatif", "Nötr", "Pozitif", "Toplam"],
                   [["Eğitim", "3.800", "3.800", "3.800", "11.400"],
                    ["Doğrulama", "200", "200", "200", "600"],
                    ["Test", "1.000", "1.000", "1.000", "3.000"],
                    ["Bir dil toplamı", "5.000", "5.000", "5.000", "15.000"]], [4.1, 2.85, 2.85, 2.85, 2.85])
    d["bert_params"] = ("Tablo 3 BERT ince ayar yapılandırması",
                        ["Parametre", "Değer"], [
                            ["Eğitim ve seçim", "3 epoch; doğrulama Macro-F1; iki dilde seçilen epoch 3"],
                            ["Tohum", "42; tek eğitim tekrarı"], ["Batch ve birikim", "16; gradyan birikimi 1; etkin batch 16"],
                            ["Öğrenme oranı", "2×10⁻⁵; doğrusal zamanlayıcı; ısınma yok"],
                            ["Eniyileyici", "AdamW; ağırlık azalımı 0,01; bias ve LayerNorm hariç"],
                            ["Uzunluk sınırı", "256 token; model konumsal kapasitesi 512"],
                            ["Sayısal hassasiyet", "FP16 autocast; gradyan norm sınırı 1,0"],
                            ["Çıkış", "Negatif, nötr ve pozitif için 3 logit"]], [4.6, 10.9])
    d["llm_params"] = ("Tablo 4 Qwen çıkarım yapılandırması",
                       ["Parametre", "Değer"], [
                           ["Model", "Qwen2.5-7B-Instruct türevi; yaklaşık 7,6B; Q4_K_M"],
                           ["Uyarlama", "Sıfır örnekli; görev için ağırlık güncellemesi yok"],
                           ["İstem", "İki dilde aynı İngilizce görev yönergesi"],
                           ["Üretim", "temperature 0; seed 42; en fazla 16 çıktı tokenı"],
                           ["Bağlam", "num_ctx 4.096"], ["Çalıştırma", "2 paralel işçi; 90 saniye zaman aşımı; en çok 3 girişim"],
                           ["Kimlik", "Aynı ağırlık digest’i ve chat template; ayrıntılar Ek A"],
                           ["Çıktı", "Tek etiket; çözümlenemeyen yanıtlar geçersiz sayılır"]], [4.6, 10.9])
    d["overall"] = ("Tablo 5 Gerçek test sonuçlarının genel karşılaştırması",
                    ["Dil", "Yöntem", "Doğru", "Yanlış", "Doğruluk", "Macro-F1"],
                    [[r["language"].upper(), r["display_name"], str(r["metrics"]["correct"]),
                      str(r["metrics"]["incorrect"]), pct(r["metrics"]["accuracy"]), num(r["metrics"]["macro_f1"])] for r in runs],
                    [1, 4.5, 2.1, 2.1, 3, 2.8])
    d["errors"] = ("Tablo 6 Gerçek duygu sınıfına göre yanlış tahmin sayıları",
                   ["Dil", "Yöntem", "Negatif", "Nötr", "Pozitif", "Toplam"],
                   [[r["language"].upper(), r["display_name"], *[str(v["incorrect"]) for v in r["classes"]], str(r["metrics"]["incorrect"])] for r in runs],
                   [1, 4.5, 2.5, 2.5, 2.5, 2.5])
    for i, lang in enumerate(["en", "tr"]):
        d["class_"+lang] = (f"Tablo {7+i} {'İngilizce' if lang == 'en' else 'Türkçe'} sınıf metrikleri",
                            ["Yöntem", "Sınıf", "Kesinlik", "Duyarlılık", "F1"],
                            [[r["display_name"], LABEL[v["class"]], num(v["precision"]), num(v["recall"]), num(v["f1"])]
                             for r in runs if r["language"] == lang for v in r["classes"]],
                            [4.5, 2.6, 2.8, 2.8, 2.8])
    d["cost"] = ("Tablo 9 Kayıtlı süreler ve ölçüm kapsamları",
                 ["Koşum", "Ölçüm", "Süre saniye"], [
                     ["EN BERT", "Optimizasyon / test çıkarımı", "116,54 / 2,46"],
                     ["TR BERT", "Optimizasyon / test çıkarımı", "119,63 / 2,74"],
                     ["EN Qwen", "Test duvarı / istek gecikmeleri toplamı", "89,56 / 178,91"],
                     ["TR Qwen", "Son oturum duvarı / tüm istek gecikmeleri", "41,79 / 507,23"],
                     ["TR Qwen", "Tam koşum duvar süresi", "Kaydedilemedi"]], [3.2, 8.1, 4.2])
    return d


FIGURES = {
    "overall": ("genel_basarim.png", "Şekil 1 Altı koşumda doğruluk ve Macro-F1", 15.2),
    "errors": ("sinif_hatalari.png", "Şekil 2 Gerçek sınıfa göre yanlış tahminler", 15.2),
    "f1": ("sinif_f1.png", "Şekil 3 Sınıf bazında F1 değerleri", 15.2),
    "distribution": ("tahmin_dagilimi.png", "Şekil 4 Yöntemlerin tahmin ettiği sınıfların dağılımı", 15.2),
    "confusion_en": ("karisiklik_en.png", "Şekil 5 İngilizce karışıklık matrisleri", 11.3),
    "confusion_tr": ("karisiklik_tr.png", "Şekil 6 Türkçe karışıklık matrisleri", 11.3),
    "learning": ("ogrenme_egrileri.png", "Şekil 7 BERT eğitim kaybı ve doğrulama başarımı", 15.2),
}


def figure(doc, key):
    filename, caption, width = FIGURES[key]
    p = para(doc)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    p.paragraph_format.line_spacing = 1
    p.paragraph_format.space_before = Pt(7)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    shape = p.add_run().add_picture(str(ROOT / "deliverables/tez_figures" / filename), width=Cm(width))
    shape._inline.docPr.set("descr", caption + "; projenin sabit tahminlerinden üretilmiştir")
    cp = para(doc, caption, "Figure Caption")
    cp.paragraph_format.keep_with_next = True
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    source = para(doc, "Kaynak: Çalışmanın deney çıktıları.", "Source Note")
    source.alignment = WD_ALIGN_PARAGRAPH.CENTER
    source.paragraph_format.keep_together = True


# Native Office Math fractions, scripts and radicals.
EQUATIONS = ["attention", "errors", "precision_recall", "f1", "aggregate", "loss"]


def mr(text):
    r = OxmlElement("m:r")
    t = OxmlElement("m:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def sub(base, index):
    e = OxmlElement("m:sSub")
    a, b = OxmlElement("m:e"), OxmlElement("m:sub")
    a.append(mr(base))
    b.append(mr(index))
    e.extend([a, b])
    return e


def sup(base, index):
    e = OxmlElement("m:sSup")
    a, b = OxmlElement("m:e"), OxmlElement("m:sup")
    a.append(mr(base))
    b.append(mr(index))
    e.extend([a, b])
    return e


def fraction(top, bottom):
    f = OxmlElement("m:f")
    a, b = OxmlElement("m:num"), OxmlElement("m:den")
    a.extend(top)
    b.extend(bottom)
    f.extend([a, b])
    return f


def root(nodes):
    r = OxmlElement("m:rad")
    props = OxmlElement("m:radPr")
    hide = OxmlElement("m:degHide")
    hide.set(qn("m:val"), "1")
    props.append(hide)
    r.append(props)
    r.append(OxmlElement("m:deg"))
    e = OxmlElement("m:e")
    e.extend(nodes)
    r.append(e)
    return r


def math_nodes(key):
    if key == "attention":
        return [mr("Attention(Q, K, V) = softmax("), fraction([mr("Q"), sup("K", "T")], [root([sub("d", "k")])]), mr(")V")]
    if key == "errors":
        return [sub("E", "c"), mr(" = "), sub("n", "c"), mr(" − "), sub("TP", "c"), mr(" = "), sub("FN", "c")]
    if key == "precision_recall":
        return [sub("P", "c"), mr(" = "), fraction([sub("TP", "c")], [sub("TP", "c"), mr(" + "), sub("FP", "c")]),
                mr("     "), sub("R", "c"), mr(" = "), fraction([sub("TP", "c")], [sub("TP", "c"), mr(" + "), sub("FN", "c")])]
    if key == "f1":
        return [sub("F1", "c"), mr(" = "), fraction([mr("2"), sub("P", "c"), sub("R", "c")], [sub("P", "c"), mr(" + "), sub("R", "c")])]
    if key == "aggregate":
        return [mr("Accuracy = "), fraction([sub("Σ", "c"), sub("TP", "c")], [mr("N")]), mr("     Macro-F1 = "),
                fraction([sub("F1", "1"), mr(" + "), sub("F1", "2"), mr(" + "), sub("F1", "3")], [mr("3")])]
    if key == "loss":
        return [sub("p", "i"), mr(" = softmax(W"), sub("h", "i"), mr(" + b)     L = −"), fraction([mr("1")], [sub("N", "train")]),
                sub("Σ", "i"), mr(" log "), sub("p", "i"), mr("("), sub("y", "i"), mr(")")]
    raise KeyError(key)


def equation(doc, key):
    p = para(doc)
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.line_spacing = 1.2
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(10)
    p.paragraph_format.keep_together = True
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    om = OxmlElement("m:oMath")
    om.extend(math_nodes(key))
    p._p.append(om)
    p.add_run("     (" + str(EQUATIONS.index(key)+1) + ")")


def cover(doc, group):
    p = para(doc, group["course"], "Subtitle")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(34)
    p.paragraph_format.space_after = Pt(52)
    p = para(doc, "İngilizce ve Türkçe Metinlerde Karşılaştırmalı Duygu Analizi", "Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    p = para(doc, "VADER BERT ve Büyük Dil Modeli Yaklaşımlarının Deneysel İncelenmesi", "Subtitle")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(30)
    p = para(doc, "Tez düzeninde ders araştırma raporu")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(26)
    for member in group["members"]:
        p = para(doc, member["name"] + "     " + member["student_number"])
        p.paragraph_format.first_line_indent = Cm(0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
    p = para(doc, "Öğretim elemanı\n" + group["instructor"])
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(25)
    p = para(doc, "Kasım 2026")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)


def front_matter(doc):
    section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_page_numbers(section, "lowerRoman")
    front_title(doc, "Özet", page=False)
    for text in ABSTRACT_TR:
        para(doc, text)
    p = para(doc, "Anahtar kelimeler Duygu analizi, VADER, BERT, BERTurk, büyük dil modelleri, nötr sınıf, Macro-F1.")
    p.paragraph_format.first_line_indent = Cm(0)
    front_title(doc, "Abstract")
    for text in ABSTRACT_EN:
        para(doc, text)
    p = para(doc, "Keywords Sentiment analysis, VADER, BERT, BERTurk, large language models, neutral class, Macro-F1.")
    p.paragraph_format.first_line_indent = Cm(0)
    p = para(doc, "İçindekiler", "Front Heading")
    p.paragraph_format.page_break_before = True
    # TOC heading uses a separate style to avoid including itself.
    if "Contents Title" not in doc.styles:
        s = doc.styles.add_style("Contents Title", 1)
        s.base_style = doc.styles["Front Heading"]
    p.style = doc.styles["Contents Title"]
    field(para(doc), 'TOC \\o "1-2" \\h \\z \\t "Front Heading,1"')
    p = para(doc, "Şekiller ve tablolar dizini", "Contents Title")
    p.paragraph_format.page_break_before = True
    field(para(doc), 'TOC \\t "Figure Caption,1" \\h \\z')
    p = para(doc, "Tablolar", "Contents Title")
    p.paragraph_format.space_before = Pt(15)
    field(para(doc), 'TOC \\t "Table Caption,1" \\h \\z')
    front_title(doc, "Kısaltmalar ve simgeler")
    rows = [
        ["BERT", "Bidirectional Encoder Representations from Transformers"],
        ["LLM", "Large Language Model / Büyük Dil Modeli"],
        ["VADER", "Valence Aware Dictionary and sEntiment Reasoner"],
        ["NLP / DDİ", "Natural Language Processing / Doğal Dil İşleme"],
        ["EN / TR", "İngilizce / Türkçe"], ["TP / FP / FN", "Doğru pozitif / yanlış pozitif / yanlış negatif"],
        ["P / R / F1", "Kesinlik / duyarlılık / harmonik ortalama"],
        ["Macro-F1", "Üç sınıfın F1 değerlerinin aritmetik ortalaması"],
        ["N / n(c) / E(c)", "Toplam test sayısı / c sınıfı desteği / c sınıfı yanlış sayısı"],
        ["SHA-256", "Veri ve model kimliği denetiminde kullanılan kriptografik özet"],
        ["FP16 / Q4_K_M", "16 bit kayan nokta / kullanılan ağırlık nicemleme biçimi"],
        ["GQA", "Grouped Query Attention / gruplanmış sorgu dikkati"],
        ["Epoch / Seed", "Eğitim verisi üzerinden tam geçiş / rastgelelik tohumu"],
    ]
    # This glossary is intentionally not in the numbered data-table list.
    table(doc, "Terimler ve simgeler", ["Kısaltma", "Açıklama"], rows, [3.7, 11.8])
    # Remove the glossary's Table Caption style from its title.
    for p in doc.paragraphs:
        if p.text == "Terimler ve simgeler":
            p.style = doc.styles["Source Note"]


def appendix(doc, manifest):
    front_title(doc, "Ekler")
    heading(doc, "Ek A Deney kimlikleri ve doğrulama izi", 2)
    para(doc, "Dosya özetleri değişiklik denetimi içindir. Aşağıdaki kimlikler, raporlanan veri ve modelleri değişebilir depo etiketlerinden ayırır. Bütün eğitim ve doğrulama bölüm özetleri data/manifest.json içinde, model ve çıktı özetleri koşum metaverilerinde saklanmaktadır.")
    for lang in ["en", "tr"]:
        ds = manifest["datasets"][lang]
        para(doc, f"{lang.upper()} veri revizyonu", "Source Note")
        para(doc, ds["revision"], "Code Block")
        para(doc, f"{lang.upper()} test CSV SHA-256", "Source Note")
        para(doc, ds["files"]["test"]["sha256"], "Code Block")
    for label, value in [
        ("EN BERT model ve tokenizer revizyonu", "86b5e0934494bd15c9632b12f734a8a67f723594"),
        ("TR BERT model ve tokenizer revizyonu", "b6e1de16c983e0f2c70664591ea3f22810072608"),
        ("Qwen ağırlık digest", "845dbda0ea48ed749caafd9e6037047aa19acfcfd82e704d7ca97d631a0b697e"),
        ("Qwen chat template SHA-256", "78b33556a364c601b7682ec3deee5536919cd9b1873cc5998a99491c6a2f2ddc"),
        ("İstem ve yapılandırmanın ortak deney özeti", "06cbb38c59dab736259c3a15e4c1daa100aadf38e40c7c0a5615843ba4236091"),
    ]:
        para(doc, label, "Source Note", keep=True)
        para(doc, value, "Code Block")
    heading(doc, "Ek B Kullanılan sabit sıfır örnekli istem", 2).paragraph_format.page_break_before = True
    para(doc, "Aşağıdaki metin iki dilin pilot ve test koşumlarında aynı kalmıştır. Bu, uygulanmış istemin tam kaydıdır; Türkçe çevirisi model girdisinde kullanılmamıştır.")
    prompt = (ROOT / "prompts/zero_shot_v1.txt").read_text(encoding="utf-8")
    for line in prompt.splitlines():
        p = para(doc, line, "Case Quote")
        p.paragraph_format.keep_with_next = True
    para(doc, "Kullanıcı mesajı şeması", "Source Note", keep=True)
    para(doc, '{"review": "Yalnızca değerlendirilecek metin"}', "Code Block")
    para(doc, "Örnek review içeriği temsili şema açıklamasıdır; yeni bir test tahmini veya istem içi etiketli gösterim değildir.", "Source Note")
    heading(doc, "Ek C Analiz dosyaları ve yeniden üretme", 2)
    para(doc, "Genel ölçümler deliverables/comparison.csv, sınıf ölçümleri deliverables/class_metrics.csv, yönlü hatalar deliverables/error_directions.csv ve nitel vakalar deliverables/error_case_studies.csv içindedir. Yeni tez görselleri deliverables/tez_figures, türetilmiş dağılım ve epoch tabloları deliverables/tez_tables altında saklanır. Ham tahminler ve JSONL kayıtları metrik hesaplamasının yeniden yapılmasına olanak verir.")
    para(doc, "Tez görsellerini üretmek için 13_build_thesis_assets.py; Word belgesini oluşturmak için 14_write_thesis.py kullanılır. Bu adımlar model eğitimi veya yeni LLM çağrısı yapmaz. Word alanları tools/finalize_thesis_word.ps1 ile güncellenir. Python ortamları ve kurulum sırası proje README belgesinde açıklanmıştır. Eğitim komutları sonuçları korumak için yeni koşum dizinleriyle kullanılmalıdır.")
    p = para(doc, "Proje deposu ")
    hyperlink(p, "github.com/tubadeligoz/duygu-analizi-odev", "https://github.com/tubadeligoz/duygu-analizi-odev")
    para(doc, "Çeviri artı VADER, çok tohumlu BERT, istem ablasyonları ve bağımsız insan kodlaması henüz uygulanmamıştır. Sunum taslağı video kaydının yerini tutmaz; video ve teslim adımları ayrıca tamamlanmalıdır.")


def build(output, group_path):
    group = json.loads(group_path.read_text(encoding="utf-8"))
    runs, unavailable = load_script("07_build_results.py").collect()
    if unavailable or len(runs) != 6:
        raise ValueError("Incomplete source results")
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    cases = read_csv(ROOT / "deliverables/error_case_studies.csv")
    data_tables = tables(runs, manifest)
    doc = Document()
    setup(doc)
    number_id = numbering(doc)
    doc.core_properties.title = "İngilizce ve Türkçe Metinlerde Karşılaştırmalı Duygu Analizi"
    doc.core_properties.subject = "VADER BERT ve Qwen yöntemlerinin tez düzeninde karşılaştırmalı araştırma raporu"
    doc.core_properties.author = "; ".join(m["name"] for m in group["members"])
    doc.core_properties.keywords = "Duygu analizi; VADER; BERT; BERTurk; Qwen; Macro-F1"
    cover(doc, group)
    front_matter(doc)
    section = doc.add_section(WD_SECTION_START.NEW_PAGE)
    set_page_numbers(section, "decimal")
    used_refs = Counter()
    for chapter_i, (title, blocks) in enumerate(CHAPTERS):
        p = heading(doc, title, 1, number_id)
        if chapter_i == 0:
            p.paragraph_format.page_break_before = False
        for kind, value in blocks:
            if kind == "p":
                para(doc, value)
                for group_str in re.findall(r"\[([\d, ]+)\]", value):
                    used_refs.update(int(v.strip()) for v in group_str.split(","))
            elif kind == "h2":
                heading(doc, value, 2, number_id)
            elif kind == "table":
                title, headers, rows, widths = data_tables[value]
                table(doc, title, headers, rows, widths)
            elif kind == "figure":
                figure(doc, value)
            elif kind == "equation":
                equation(doc, value)
            elif kind == "case":
                case = cases[value]
                p = para(doc, f"Vaka {value+1} {case['category']}", "Heading 3")
                para(doc, f"{case['language'].upper()} · {case['method']} · Kaynak {LABEL[case['label']]} · Tahmin {LABEL[case['prediction']]}", "Source Note", keep=True)
                para(doc, case["text"], "Case Quote")
                p = para(doc, "Kayıt kimliği " + case["id"], "Code Block")
                p.paragraph_format.keep_together = True
    if set(used_refs) != set(range(1, len(REFERENCES)+1)):
        raise ValueError(f"Uncited/missing bibliography references: {set(range(1,len(REFERENCES)+1))-set(used_refs)}")
    front_title(doc, "Kaynakça")
    para(doc, "Metin içinde numaralı atıf sistemi kullanılmıştır. Çevrim içi model ve veri kartlarında 2026, erişim yılını belirtir; modelin yayımlanma yılı olarak yorumlanmamalıdır. Teknik kaynaklara erişim tarihi 22 Kasım 2026’dır.", "Source Note")
    for item in REFERENCES:
        p = para(doc, formatted(item), "Reference")
        p.add_run(" ")
        hyperlink(p, "Çevrim içi kaynak", item[-1])
    appendix(doc, manifest)
    # Remove any inherited paragraph borders from every story before writing.
    for part in [doc.part, *[s.header.part for s in doc.sections], *[s.footer.part for s in doc.sections]]:
        for border in list(part.element.iter(qn("w:pBdr"))):
            border.getparent().remove(border)
    output.parent.mkdir(parents=True, exist_ok=True)
    doc.save(output)
    prose = " ".join([*ABSTRACT_TR, *ABSTRACT_EN, *[v for _, blocks in CHAPTERS for k, v in blocks if k == "p"]])
    stats = {"built_at_utc": utc_now(), "audience": group["audience"], "output": str(output.relative_to(ROOT)),
             "sha256_before_field_update": sha256(output), "chapters": len(CHAPTERS),
             "academic_and_technical_references": len(REFERENCES), "cited_reference_count": len(used_refs),
             "main_narrative_words_including_abstracts": len(prose.split()),
             "numbered_tables": len(data_tables), "figures": len(FIGURES), "equations": len(EQUATIONS),
             "experiments_added": 0, "source_predictions": {r["predictions_path"]: r["predictions_sha256"] for r in runs}}
    dest = ROOT / "audit" / ("thesis_build_public.json" if group["audience"] == "public" else "thesis_build_submission.local.json")
    # The private build log contains no student IDs, but stays with private artifacts.
    if group["audience"] != "public":
        dest = output.parent / "thesis_build.json"
    dest.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in stats.items() if k != "source_predictions"}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="deliverables/Proje_Raporu_Tez.docx")
    parser.add_argument("--group-info", default="configs/group_members.public.json")
    args = parser.parse_args()
    build(ROOT / args.output, ROOT / args.group_info)
