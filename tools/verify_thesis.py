"""Audit thesis structure, frozen inputs, privacy, populated fields and page parity.

The visual review is recorded separately after inspecting the rendered pages.
Requires the bundled document runtime (python-docx, pypdf, Pillow).
"""
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from docx import Document
from lxml import etree
from PIL import Image
from pypdf import PdfReader

from experiment_utils import load_script, sha256, utc_now
from thesis_references import REFERENCES


def require(condition, message):
    if not condition:
        raise ValueError(message)


def inspect(path):
    doc = Document(path)
    with zipfile.ZipFile(path) as archive:
        xml_parts = [archive.read(n).decode("utf-8") for n in archive.namelist() if n.endswith(".xml")]
        xml = archive.read("word/document.xml")
    root = etree.fromstring(xml)
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
          "m": "http://schemas.openxmlformats.org/officeDocument/2006/math"}
    text = " ".join(root.xpath("//w:t/text()", namespaces=ns))
    refs = [p.text for p in doc.paragraphs if p.style.name == "Reference"]
    require(len(refs) == len(REFERENCES) == 33, "Reference count mismatch")
    require([int(re.match(r"\[(\d+)\]", p)[1]) for p in refs] == list(range(1, 34)), "Bibliography numbering mismatch")
    require(len(root.xpath("//m:oMath", namespaces=ns)) == 6, "Missing native equations")
    require(len(doc.inline_shapes) == 7, "Figure count mismatch")
    require(len([p for p in doc.paragraphs if p.style.name == "Table Caption"]) == 9, "Table count mismatch")
    require(len([p for p in doc.paragraphs if p.style.name == "Figure Caption"]) == 7, "Caption count mismatch")
    require(len(root.xpath('//w:instrText[contains(., "TOC")]', namespaces=ns)) == 3, "Missing TOC fields")
    require("w:pBdr" not in xml.decode(), "Unexpected decorative title rule")
    require("0804.1475" not in " ".join(xml_parts), "Incorrect source URL remains")
    require("꜀" not in text, "Invalid subscript glyph remains")
    return doc, text, " ".join(xml_parts)


def main():
    public = ROOT / "deliverables/Proje_Raporu_Tez.docx"
    private = ROOT / "teslim_ozel/Proje_Raporu_Tez.docx"
    pd, pt, px = inspect(public)
    sd, st, sx = inspect(private)
    group = json.loads((ROOT / "configs/group_members.local.json").read_text(encoding="utf-8"))
    for member in group["members"]:
        require(member["student_number"] not in px, "Student number in public report")
        require(member["student_number"] in sx, "Student number missing in submission report")
    require(pt[pt.index("Özet"):] == st[st.index("Özet"):], "Public and private report bodies differ")
    frozen = load_script("00_audit.py").audit_data(ROOT / "data")
    runs, unavailable = load_script("07_build_results.py").collect()
    require(frozen["all_checks_passed"] and not unavailable and len(runs) == 6, "Frozen results failed verification")

    ppdf = PdfReader(ROOT / "qa/tez_final_public/rapor.pdf")
    spdf = PdfReader(ROOT / "qa/tez_final_submission/rapor.pdf")
    require(len(ppdf.pages) == len(spdf.pages), "Different report page counts")
    page_count = len(ppdf.pages)
    require(page_count > 25, "Unexpectedly short thesis report")
    pdf_text = " ".join(p.extract_text() for p in ppdf.pages)
    for phrase in ["Error! Reference source not found", "Error! No table of contents entries found", "Başvuru kaynağı bulunamadı"]:
        require(phrase not in pdf_text, "Broken Word field")
    require("Şekil 7 BERT eğitim" in pdf_text, "Unpopulated figure list")
    require("Tablo 9 Kayıtlı" in pdf_text, "Unpopulated table list")
    pixel_checks = []
    for i in range(2, page_count+1):
        a = ROOT / f"qa/tez_final_public/pages/page-{i}.png"
        b = ROOT / f"qa/tez_final_submission/pages/page-{i}.png"
        with Image.open(a) as pa, Image.open(b) as pb:
            require(pa.size == pb.size, "Page dimensions differ")
            ah = hashlib.sha256(pa.tobytes()).hexdigest()
            bh = hashlib.sha256(pb.tobytes()).hexdigest()
            require(ah == bh, f"Page {i} differs between report versions")
            pixel_checks.append(i)
    counts = [len(p.extract_text().split()) for p in ppdf.pages]
    require(all(n > 35 for n in counts), "Nearly empty report page")
    result = {"verified_at_utc": utc_now(), "all_structural_checks_passed": True,
              "pages": page_count, "references": len(REFERENCES), "figures": 7, "tables": 9, "native_equations": 6,
              "public_sha256": sha256(public), "submission_sha256": sha256(private),
              "student_numbers_publicly_visible": False, "private_cover_has_all_three_student_numbers": True,
              "bodies_text_identical": True, "identical_body_page_pixels": pixel_checks,
              "frozen_data_unchanged": True, "test_runs_verified": 6, "test_predictions_verified": 18000,
              "pdf_page_word_counts": counts, "visual_review": "Recorded separately in audit/thesis_visual_qa.json"}
    (ROOT / "audit/thesis_document_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ["all_structural_checks_passed", "pages", "references", "figures", "tables", "native_equations", "student_numbers_publicly_visible", "frozen_data_unchanged"]}))


if __name__ == "__main__":
    main()
