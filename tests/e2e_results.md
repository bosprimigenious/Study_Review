# E2E Results

Date: 2026-06-10
Fixture: `tests/fixtures/computer-network`

## 6-step chain

| Step | Exit | Seconds |
|------|------|---------|
| Q1_init | 0 | 0.111 |
| Q2_analyze | 0 | 0.146 |
| Q3_generate | 0 | 0.147 |
| Q4_plan | 0 | 0.162 |
| session | 0 | 0.279 |
| Q8_due | 0 | 0.142 |

Non-interactive chain total (excl. session): **0.708s** (budget ≤15s)

## Epic 6 checks

- 6-01 chain exit 0: **PASS**
- 6-02 review 8 files + fixture clean: **PASS**
- 6-03 analysis priorities/evidence: **PASS**
- 6-04 generated questions quality: **PASS**
- 6-05 plan executable: **PASS**
- 6-06 mistake loop: **PASS**

## Q1–Q12 metrics

| Q | Metric | Threshold | Actual | Pass |
|---|--------|-----------|--------|------|
| Q1_init | | 2 | 0.111 | PASS |
| Q2_analyze | | 3 | 0.146 | PASS |
| Q3_generate | | 5 | 0.147 | PASS |
| Q4_plan | | 3 | 0.162 | PASS |
| Q5_time_to_first_question | | 90 | 0.987 | PASS |
| Q6_grading_accuracy | deferred | — | — | 待 v0.2 |
| Q7_mistake_log_latency | manual | ≤60s | sync | PASS |
| Q8_due_today | | 2 | 0.142 | PASS |
| Q9_scoring_points_coverage | | 100% | True | PASS |
| Q10_evidence_trace | | 100% | True | PASS |
| Q11_id_unique | | 100% | True | PASS |
| Q12_bad_yaml_tolerance | | 100% | 0.168 | PASS |

## Details

```json
{
  "date": "2026-06-10",
  "timings_sec": {
    "Q1_init": 0.111,
    "Q2_analyze": 0.146,
    "Q3_generate": 0.147,
    "Q4_plan": 0.162,
    "session": 0.279,
    "Q8_due": 0.142,
    "Q5_time_to_first_question": 0.987
  },
  "exit_codes": {
    "Q1_init": 0,
    "Q2_analyze": 0,
    "Q3_generate": 0,
    "Q4_plan": 0,
    "session": 0,
    "Q8_due": 0
  },
  "checks": {
    "all_pass": true,
    "details": {
      "review_files": [
        "cards.yaml",
        "exam-analysis.yaml",
        "files.yaml",
        "generated-questions.yaml",
        "mistake-log.md",
        "past-exam-patterns.yaml",
        "plan.md",
        "progress.md"
      ],
      "review_files_ok": true,
      "priorities_count": 3,
      "priorities_ok": true,
      "evidence_ok": true,
      "q10_evidence_trace": true,
      "questions_count": 5,
      "q9_scoring_points": true,
      "no_forbidden_words": true,
      "plan_sections_ok": true,
      "now_single_action": true,
      "mistake_cards": 1,
      "mistake_log_ok": true,
      "due_loop_ok": true,
      "fixture_material_files": [
        "6-Transport(3).pptx",
        "期末复习重点.pdf",
        "计算机网络样题(5).pdf"
      ],
      "fixture_course_files_clean": true,
      "review_only_under_fixture": true
    }
  },
  "metrics": {
    "Q1_init": {
      "threshold_sec": 2,
      "actual_sec": 0.111,
      "pass": true
    },
    "Q2_analyze": {
      "threshold_sec": 3,
      "actual_sec": 0.146,
      "pass": true
    },
    "Q3_generate": {
      "threshold_sec": 5,
      "actual_sec": 0.147,
      "pass": true
    },
    "Q4_plan": {
      "threshold_sec": 3,
      "actual_sec": 0.162,
      "pass": true
    },
    "Q5_time_to_first_question": {
      "threshold_sec": 90,
      "actual_sec": 0.987,
      "pass": true
    },
    "Q6_grading_accuracy": {
      "status": "deferred",
      "note": "待 v0.2 单元测试覆盖"
    },
    "Q7_mistake_log_latency": {
      "status": "manual_ok",
      "note": "session 同步落盘，due 立即可见"
    },
    "Q8_due_today": {
      "threshold_sec": 2,
      "actual_sec": 0.142,
      "pass": true
    },
    "Q9_scoring_points_coverage": {
      "threshold": "100%",
      "pass": true
    },
    "Q10_evidence_trace": {
      "threshold": "100%",
      "pass": true
    },
    "Q11_id_unique": {
      "threshold": "100%",
      "pass": true
    },
    "Q12_bad_yaml_tolerance": {
      "threshold": "100%",
      "pass": true,
      "actual_sec": 0.168
    }
  },
  "chain_total_sec": 0.708
}
```
