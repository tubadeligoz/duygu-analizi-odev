"""Rasterize native Word's PDF for visual QA using the bundled document runtime."""
import argparse
import json
from pathlib import Path

import pypdfium2 as pdfium

p = argparse.ArgumentParser()
p.add_argument("pdf")
p.add_argument("output")
args = p.parse_args()
out = Path(args.output)
out.mkdir(parents=True, exist_ok=True)
pdf = pdfium.PdfDocument(args.pdf)
for i in range(len(pdf)):
    page = pdf[i]
    image = page.render(scale=1.7).to_pil()
    image.save(out / f"page-{i + 1}.png")
    page.close()
print(json.dumps({"pages": len(pdf), "output": str(out)}))
pdf.close()
