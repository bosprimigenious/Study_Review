# PDF and Image OCR Workflow

This document records how Study Review should process local PDF materials, especially scanned or image-based exam papers.

## Goal

The goal is not "perfect PDF parsing". The goal is:

```text
visible local PDF
  -> page images when needed
  -> text extraction or OCR
  -> course-local OCR text files
  -> exam analysis with source traceability
  -> manual image verification for formulas
```

This workflow is especially important for past exams because MVP priorities should be based on real exam papers, not only slide filenames or general model memory.

## Source Policy

All extraction must stay inside the local workspace.

Use:

```text
/Users/bosprimigenious/Important_FIles/2025-2026下
```

Do not use external websites or cloud OCR for course-content extraction unless the user explicitly allows it.

## Current Use Case

For `概率论与数理统计`, the target inputs are local PDFs such as:

```text
概率论与数理统计/02_期末试卷/*.pdf
```

The expected text outputs are:

```text
概率论与数理统计/05_OCR文本/全部PDF/
概率论与数理统计/05_OCR文本/期末试卷/
```

The first directory stores OCR/text output for all visible PDFs under the course. The second stores a focused copy for final-exam papers.

## Processing Strategy

Use a hybrid strategy.

### 1. Scan Visible PDFs

First collect all visible PDF files under the course folder.

Rules:

- Include PDFs in course subfolders.
- Prefer `02_期末试卷` for exam-priority analysis.
- Ignore hidden files and system artifacts.
- Keep original PDFs unchanged.

### 2. Try Native PDF Text First

Some PDFs have a real text layer. Extract that first because it is faster and cleaner than OCR.

Recommended local script:

```text
scripts/ocr/extract_pdf_text.swift
```

Expected behavior:

- input: one PDF path or a PDF directory
- output: one text file per PDF
- preserve page boundaries
- include source PDF path in the text header
- reject unreliable PDF text pages and fall back to Vision OCR

### 2.1 Detect Garbled PDF Text

Do not trust native PDF text just because it exists. Many math PDFs contain a broken text layer where Chinese text is readable but formulas become replacement characters or fragmented symbols.

Reject a page's PDF text when any of these are true:

- text is too short to be useful
- replacement character `�` appears frequently
- readable Chinese/letter/digit ratio is too low
- many lines contain only one to three symbol fragments

Rejected pages should be marked like this:

```text
[method: vision-ocr]
[pdf-text rejected: replacement-character-heavy, replacementRatio=..., readableRatio=..., shortLineRatio=...]
```

Then render the page and OCR the image.

### 3. Render Image Pages When Needed

For scanned PDFs or pages with weak text extraction, render pages into images.

Recommended local script:

```text
scripts/ocr/render_pdf_pages.swift
```

Expected behavior:

- input: PDF path
- output: page images under `/tmp` or a course OCR temp directory
- support scale factor for readability, such as `2.0`
- never modify original PDF

### 4. OCR Image Pages With macOS Vision

For image pages, use local macOS Vision OCR.

Recommended local script:

```text
scripts/ocr/ocr_pdf.swift
```

Expected behavior:

- run OCR page by page
- preserve page numbers
- write text output to the course OCR folder
- mark low-confidence or garbled regions when possible

### 5. Batch Extract Course PDFs

For a course-level run, use one wrapper script.

Recommended local script:

```text
scripts/ocr/extract_probability_pdfs.swift
```

Expected behavior:

- scan all visible PDFs under `概率论与数理统计`
- run native text extraction where possible
- run OCR for image/scanned pages
- write all outputs under `05_OCR文本`
- duplicate or group final-exam OCR output under `05_OCR文本/期末试卷`

## Output Naming

Use stable filenames so later scripts can trace OCR text back to original PDFs.

Recommended pattern:

```text
05_OCR文本/全部PDF/
  2025-2026 第一学期 概率论与数理统计 期末试卷【A卷】.txt

05_OCR文本/期末试卷/
  2025-2026 第一学期 概率论与数理统计 期末试卷【A卷】.txt
```

Each text file should start with metadata:

```text
Source PDF: 概率论与数理统计/02_期末试卷/...
Extraction: native-text | vision-ocr | mixed
Generated at: YYYY-MM-DD HH:mm
Pages: N
```

Then use page separators:

```text
--- Page 1 ---
...

--- Page 2 ---
...
```

## Exam Analysis Priority

When analyzing重点, rank evidence by source type:

```text
final exams / past exams
  -> sample papers
  -> homework answers
  -> teacher focus
  -> review PDFs
  -> slides
  -> notes
```

For probability and statistics, true exam priority should come from recent final papers first.

Example:

```text
2025-2026 final
2024-2025 final
2023-2024 final
2022-2023 final
2020-2021 final
```

Then summarize repeated patterns:

- chapter
- topic
- question type
- small question vs big question
- repeated wording
- formula/condition requirements
- evidence PDF and page

## Formula and Math Caveats

OCR is useful but not fully reliable for formulas.

Common OCR errors:

- `∪`, `∩`, `⊂`, `⊆` confused with letters or punctuation
- superscripts and subscripts lost
- fractions flattened
- Greek letters misread
- `P(A|B)` misread as `P(AIB)` or similar
- matrices and multi-line formulas broken

Therefore:

- Use OCR text for topic discovery and rough question grouping.
- Use original page images to verify formula-heavy questions.
- When a formula matters, cite the PDF and page and manually check the rendered image.
- Do not generate confident exam claims from garbled OCR alone.

## Integration With Study Review

The OCR outputs should become local materials for analysis.

Recommended `files.yaml` entries:

```yaml
files:
  - id: prob-exam-2025-a-pdf
    path: 概率论与数理统计/02_期末试卷/2025-2026 第一学期 概率论与数理统计 期末试卷【A卷】.pdf
    material_type: past_exam
    status: ready

  - id: prob-exam-2025-a-ocr
    path: 概率论与数理统计/05_OCR文本/期末试卷/2025-2026 第一学期 概率论与数理统计 期末试卷【A卷】.txt
    material_type: past_exam
    status: ready
    notes: OCR text extracted from the matching PDF.
```

`analyze_exam.py` should later prefer OCR text when it exists, while keeping the PDF path as the source of truth.

## Recommended Analysis Output

For each extracted exam pattern, keep evidence.

```yaml
patterns:
  - topic: 事件运算与概率公式
    chapter: 第一章
    question_type: fill_blank_or_choice
    frequency: 4
    evidence:
      - source_file: 概率论与数理统计/02_期末试卷/2024-2025 第一学期 概率论与数理统计 期末试卷【A卷】.pdf
        ocr_file: 概率论与数理统计/05_OCR文本/期末试卷/2024-2025 第一学期 概率论与数理统计 期末试卷【A卷】.txt
        page: 1
        question_hint: 第 1 题，三事件并
```

## Manual Review Checklist

After a batch OCR run, check:

- Total scanned PDFs count.
- Total OCR text files count.
- Whether final-exam PDFs have focused copies under `05_OCR文本/期末试卷`.
- Whether page counts roughly match original PDFs.
- Whether formulas on high-value questions were verified from rendered images.
- Whether the analysis cites local PDFs and OCR text instead of unsupported memory.

## Product Implication

This capability should eventually become a paid or high-value product path:

```text
上传/选择往年题
  -> 自动 OCR
  -> 识别高频题型
  -> 匹配资料章节
  -> 生成变式题
  -> 生成今晚保底计划
```

In the UI, this should surface as:

```text
分析往年题
```

not as a generic "OCR" feature. The user cares about what to review, not the extraction technology.

## Current Limitations

- OCR quality depends on PDF scan clarity.
- Formula extraction must be manually verified.
- Native text extraction and OCR outputs may disagree.
- Current Study Review MVP can document and consume OCR text, but should not pretend formula-heavy OCR is perfect.
- Batch scripts should remain local and repeatable before being wrapped into backend jobs.
