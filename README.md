# PDFMerger Desktop Lite

PDFMerger Desktop Lite is a small local desktop app for merging PDF files without using the web app. It is separate from the main PDFMerger project and lives in its own folder so it can be developed, packaged, or shared independently.

## Part of PDFMerger

PDFMerger is a practical document toolkit by Manjurul Islam, built around a simple idea: PDF tools should be fast,
private, and easy to use.

For the full browser-based toolkit, visit:

[https://www.mergepdfs.co.uk/](https://www.mergepdfs.co.uk/)

The main web app includes additional tools for everyday document work, while this desktop edition focuses on one
job: merging PDFs locally from your computer.

## What It Does

- Add individual PDF files or load every PDF from a folder.
- Reorder files with drag-and-drop or Move up / Move down buttons.
- Remove files or clear the list before merging.
- Choose output page size: original, A5, A4, A3, Letter, Legal, or Tabloid.
- Choose orientation: keep original, portrait, or landscape.
- Choose quality mode: Best quality, Balanced, or Small file.
- Save the merged PDF locally on your computer.

## Privacy Model

This desktop version processes files on your machine. It does not upload PDFs, call a PDFMerger server, create an account, or store document content outside the output file you choose to save.

## Requirements

- Python 3.9 or newer
- tkinter, included with most Python installations
- pypdf

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run the app:

```powershell
python pdfmerger_desktop.py
```

On Windows, you can also double-click `run_pdfmerger.bat` after installing Python and dependencies. The launcher tries
the Windows `py` launcher first, then `python`.

## Optional EXE Build

If you want a single Windows executable:

```powershell
python -m pip install pyinstaller
pyinstaller --onefile --windowed --name PDFMerger-Desktop-Lite pdfmerger_desktop.py
```

The executable will be created in the `dist` folder.

## Project Files

```text
pdfmerger-desktop-lite/
  pdfmerger_desktop.py
  requirements.txt
  run_pdfmerger.bat
  README.md
  LICENSE
  NOTICE.md
```

## Notes

The app is intentionally lightweight. It focuses on the most useful desktop merge workflow rather than the full web toolkit. PDF conversion, OCR, and cloud connectors are better handled by the main PDFMerger web app.
