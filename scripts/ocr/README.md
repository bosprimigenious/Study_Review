# OCR Scripts

Local macOS Swift helpers for PDF text extraction, PDF page rendering, and Vision OCR.

These scripts are optional helpers for scanned or image-heavy course materials. They should be used when `analyze_exam.py` needs better local text evidence than filenames and `files.yaml` metadata.

## Scripts

```text
extract_pdf_text.swift
  Extract one PDF into text. Uses native PDF text when available, with Vision OCR fallback for image-only pages.

extract_probability_pdfs.swift
  Batch extract visible PDFs under one input root into an output root. Built for course-level probability/statistics extraction.

render_pdf_pages.swift
  Render each PDF page to PNG images for manual formula verification.

render_selected_exam_pages.swift
  Render the curated probability/statistics exam set to JPEG images for batch source checking.

ocr_pdf.swift
  Force OCR every page of one PDF and write text output.

ocr_image.swift
  OCR one image and print recognized text.
```

## Examples

In restricted environments, set the clang module cache under `/tmp`:

```bash
export CLANG_MODULE_CACHE_PATH=/tmp/study-review-clang-cache
```

Extract one PDF:

```bash
swift scripts/ocr/extract_pdf_text.swift "input.pdf" "output.txt" 2.2
```

Batch extract a course folder:

```bash
swift scripts/ocr/extract_probability_pdfs.swift "../概率论与数理统计" "../概率论与数理统计/05_OCR文本/全部PDF" 2.0
```

Render one PDF for visual checking:

```bash
swift scripts/ocr/render_pdf_pages.swift "input.pdf" "/tmp/pdf-pages" 2.0
```

Render the curated probability/statistics exam set:

```bash
swift scripts/ocr/render_selected_exam_pages.swift "../概率论与数理统计/02_期末试卷" "/tmp/prob-exam-pages" 2.0
```

Force OCR one PDF:

```bash
swift scripts/ocr/ocr_pdf.swift "input.pdf" "output.txt" 2.5
```

OCR one rendered image:

```bash
swift scripts/ocr/ocr_image.swift "/tmp/pdf-pages/page-01.png" "zh-Hans,en-US"
```

## Caveats

- OCR stays local through macOS Vision.
- Formula-heavy pages still need rendered-image verification.
- `extract_pdf_text.swift` and `extract_probability_pdfs.swift` reject garbled native PDF text and fall back to Vision OCR.
- Rejection checks include replacement characters, low readable-character ratio, and fragmented symbol-only lines.
- These scripts should not modify original course PDFs.
- Use OCR text for topic discovery and grouping, not as unquestioned formula truth.
