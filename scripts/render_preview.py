#!/usr/bin/env python3
"""Render a DOCX to PDF and PNGs in an isolated conversion directory."""
import argparse
from pathlib import Path
import re
import shutil
import subprocess
import tempfile


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('docx', type=Path)
    ap.add_argument('outdir', nargs='?', type=Path)
    args = ap.parse_args()
    src = args.docx.resolve()
    out = args.outdir or src.parent / 'preview'
    if not src.is_file():
        ap.error(f'Input does not exist: {src}')
    exe = shutil.which('soffice') or shutil.which('libreoffice')
    if not exe or not shutil.which('pdfinfo') or not shutil.which('pdftoppm'):
        ap.error('Preview requires LibreOffice, pdfinfo and pdftoppm on PATH.')
    out.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix='resume-preview-') as folder:
            tmp = Path(folder)
            profile = (tmp / 'profile').as_uri()
            subprocess.run([exe, f'-env:UserInstallation={profile}', '--headless',
                            '--convert-to', 'pdf', '--outdir', str(tmp), str(src)],
                           check=True, capture_output=True, timeout=180)
            pdf = tmp / (src.stem + '.pdf')
            if not pdf.is_file():
                ap.error('Conversion produced no PDF.')
            info = subprocess.run(['pdfinfo', str(pdf)], check=True,
                                  capture_output=True, text=True, timeout=30).stdout
            pages = re.search(r'Pages:\s+(\d+)', info)
            subprocess.run(['pdftoppm', '-png', '-r', '100', str(pdf), str(tmp / 'page')],
                           check=True, capture_output=True, timeout=180)
            images = sorted(tmp.glob('page-*.png'))
            if not images:
                ap.error('Rendering produced no page images.')
            shutil.copy2(pdf, out / pdf.name)
            for old in out.glob('page-*.png'):
                if re.fullmatch(r'page-\d+\.png', old.name):
                    old.unlink()
            for image in images:
                shutil.copy2(image, out / image.name)
            print('PDF:', out / pdf.name)
            print('Pages:', pages.group(1) if pages else '?')
            for image in images:
                print('Image:', out / image.name)
    except (OSError, subprocess.SubprocessError) as exc:
        ap.error(f'Preview failed: {exc}')


if __name__ == '__main__':
    main()
