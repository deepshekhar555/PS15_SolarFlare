"""Generate a short PDF summary for hackathon submission.
Includes README summary text and available plots.
"""
from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
from PIL import Image

ROOT = Path('D:/PS15_SolarFlare')
OUT = ROOT / 'output'
OUT.mkdir(parents=True, exist_ok=True)

readme = (ROOT / 'README.md').read_text()
plots = [OUT / p for p in ['solexs_plot_20260606.png', 'solexs_plot_zoom.png']]

pdf_path = OUT / 'submission_summary.pdf'
with PdfPages(pdf_path) as pdf:
    # Page 1: Title + README excerpt
    fig = plt.figure(figsize=(8.27, 11.69))  # A4
    fig.suptitle('PS15_SolarFlare — Summary', fontsize=16)
    txt = '\n'.join(readme.splitlines()[:40])  # take first 40 lines
    plt.axis('off')
    plt.text(0.01, 0.98, txt, va='top', wrap=True, fontsize=10)
    pdf.savefig(fig)
    plt.close()

    # Page 2+: plots
    for p in plots:
        if p.exists():
            img = Image.open(p)
            fig = plt.figure(figsize=(8.27, 11.69))
            plt.axis('off')
            plt.imshow(img)
            pdf.savefig(fig)
            plt.close()

print(f'Wrote PDF: {pdf_path}')
