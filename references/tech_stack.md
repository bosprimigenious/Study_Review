# Tech Stack

This document records the recommended technical stack for turning Study Review from a local CLI skill into a modern exam-review workspace.

## Positioning

The product should feel like a focused, modern workbench:

```text
upload materials
  -> analyze past exams
  -> generate tonight's plan
  -> start five-question diagnosis
  -> log mistakes
  -> review due items
```

The stack should optimize for:

- polished SaaS/workbench UI
- fast MVP delivery
- clear frontend/backend boundaries
- local-first course data
- future agent orchestration
- PDF and scanned-exam processing

## Recommended MVP Stack

Use this combination for the first full product version:

```text
Frontend:
  Vite
  React
  TypeScript
  Tailwind CSS
  shadcn/ui
  Radix UI
  lucide-react

State and data:
  TanStack Query
  Zustand
  Zod
  React Hook Form

Files and previews:
  react-dropzone
  react-pdf

Charts and progress:
  recharts

Backend:
  FastAPI
  Pydantic
  PyYAML
  SQLite

PDF / OCR:
  PyMuPDF
  pdfplumber
  python-pptx
  macOS Vision OCR via Swift scripts
```

## Frontend

### React + TypeScript + Vite

Use for the first frontend app.

Why:

- fast local dev
- simple build setup
- strong TypeScript support
- easier than Next.js for a local-first MVP

Use Next.js later only if the product needs server rendering, auth-heavy flows, public pages, or hosted multi-user deployment.

### Tailwind CSS

Use for layout, spacing, color, and responsive styling.

Rules:

- keep spacing consistent
- avoid one-off CSS when a token can express it
- avoid heavy gradients and decorative backgrounds
- use subtle status colors for risk, urgency, and completion

### shadcn/ui + Radix UI

Use for product-grade components:

- buttons
- dialogs
- tabs
- dropdowns
- popovers
- command menus
- forms
- toasts
- sidebars
- progress states

Why:

- modern SaaS/workbench feel
- accessible primitives from Radix
- easy to customize with Tailwind
- consistent with Linear/Vercel/Feishu-style product surfaces

### lucide-react

Use for icons.

Rules:

- use icons in buttons when the action is common
- keep icon stroke width consistent
- avoid custom SVG unless the icon does not exist
- use tooltips for less obvious icon-only actions

## State and Data

### TanStack Query

Use for backend requests and caching:

- courses
- materials
- exam analysis
- generated questions
- review sessions
- mistake logs
- due items

It should own server state. Avoid duplicating server state in Zustand.

### Zustand

Use for small client-side UI state:

- selected course
- sidebar collapsed state
- active review session id
- current workspace mode
- temporary UI preferences

Do not use Zustand as a database.

### Zod

Use for API schema validation.

Shared schema targets:

- `Course`
- `MaterialFile`
- `ExamAnalysis`
- `GeneratedQuestion`
- `ReviewPlan`
- `ReviewSession`
- `MistakeEntry`
- `DueItem`

### React Hook Form

Use for:

- upload material metadata
- create course
- set exam date
- set daily time budget
- set goal: pass or high score

Pair with Zod validation.

## Files and Uploads

### react-dropzone

Use for uploading or registering:

- PPT
- PDF
- Word
- Markdown
- images
- zip files
- past exams
- teacher focus files

The upload UI should ask the user to confirm file type:

```text
slides
past_exam
mock_exam
homework_answer
teacher_focus
notes
textbook
other
```

### react-pdf

Use for PDF preview in the frontend.

Use cases:

- preview past exam pages
- show source evidence beside generated priorities
- let the user verify formula-heavy OCR regions

Do not make PDF preview the main workflow. The main workflow is still "analyze past exams" and "start review".

## Charts and Progress

### recharts

Use only for useful review metrics:

- material analysis coverage
- high-frequency topic distribution
- mistake type distribution
- today's progress
- plan completion

Avoid decorative charts. The product value is action, not analytics theater.

## Motion

### framer-motion

Optional.

Use sparingly for:

- button feedback
- card entrance
- task completion
- review-session transitions

Do not use large animated backgrounds or decorative motion.

## Backend

### FastAPI

Use for the Python backend.

Recommended endpoints:

```text
GET  /courses
GET  /courses/{course}/state
POST /courses/{course}/init-review
POST /courses/{course}/materials
POST /courses/{course}/exam-analysis
POST /courses/{course}/questions
POST /courses/{course}/plan
POST /review-session/start
POST /review-session/answer
POST /mistakes
GET  /due-today
POST /agent/run
```

### Pydantic

Use for request and response models.

The backend should validate:

- course id
- material file type
- generated question structure
- review plan tasks
- mistake log fields
- due item dates

### PyYAML

Use while the product is still local-first and file-based.

It should read/write:

- `files.yaml`
- `cards.yaml`
- `exam-analysis.yaml`
- `past-exam-patterns.yaml`
- `generated-questions.yaml`

### SQLite

Introduce SQLite after the CLI and API contracts are stable.

Use SQLite for:

- courses
- material files
- exam analyses
- generated questions
- cards
- mistakes
- review sessions
- agent runs

Do not start with PostgreSQL unless the product becomes multi-user and hosted.

## PDF and OCR

### PyMuPDF

Use for:

- PDF page count
- lightweight text extraction
- rendering pages to images when Python-side rendering is enough
- extracting page-level metadata

### pdfplumber

Use for:

- text-heavy PDFs
- table-like exam layouts
- page-level text extraction

### python-pptx

Use for:

- PPTX slide text extraction
- slide title detection
- basic slide metadata

### macOS Vision OCR via Swift

Use for scanned or image-based PDFs on local macOS.

Related workflow:

```text
references/pdf_ocr_workflow.md
```

Recommended local scripts:

```text
scripts/ocr/extract_pdf_text.swift
scripts/ocr/render_pdf_pages.swift
scripts/ocr/ocr_pdf.swift
scripts/ocr/extract_probability_pdfs.swift
```

Use OCR text for topic discovery and question grouping. Verify formula-heavy questions against rendered page images.

## Agent Layer

MVP should stay Python-first:

```text
single StudyReviewOrchestrator
  -> deterministic Python tools
  -> YAML/Markdown or SQLite state
  -> optional LLM grading/generation later
```

Do not begin with multiple autonomous agents.

Use:

- `references/orchestrator.md` for runtime contract
- `references/agent_development_plan.md` for engineering plan
- `SKILL.md` as behavior policy

Only consider OpenAI Agents SDK or LangGraph after:

- CLI tools have JSON output
- FastAPI endpoints are stable
- review sessions need resumable state
- evals show prompt-only orchestration is hard to debug

## UI Direction

For open-source benchmarks, per-page copy targets, and demo links, see `references/ui_references.md`.

The frontend should feel like:

```text
Notion clarity
Linear precision
Feishu workbench density
Vercel-style restraint
```

Main screen should prioritize:

- upload materials
- analyze past exams
- generate tonight's pass plan
- start five-question diagnosis
- continue due review

Avoid:

- empty landing-page hero sections
- decorative dashboards
- excessive charts
- full-screen grid backgrounds
- chat as the primary entry point

## Recommended First Implementation

Start with:

```text
Vite + React + TypeScript
Tailwind CSS
shadcn/ui
lucide-react
TanStack Query
Zustand
React Hook Form + Zod
react-dropzone
recharts
FastAPI + Pydantic + SQLite
```

Then add:

```text
react-pdf
PyMuPDF
pdfplumber
python-pptx
macOS Vision OCR scripts
```

The first frontend should be a review workbench, not a marketing page.
