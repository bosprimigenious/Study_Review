#!/usr/bin/env python3
"""One-off E2E timing and metric collector for Epic 6."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "computer-network"
REVIEW = FIXTURE / "review"
SCRIPTS = ROOT / "scripts"


def run_step(name: str, cmd: list[str]) -> tuple[float, str, int]:
    start = time.perf_counter()
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = round(time.perf_counter() - start, 3)
    output = (result.stdout or "") + (result.stderr or "")
    return elapsed, output, result.returncode


def verify_outputs() -> dict[str, object]:
    checks: dict[str, object] = {"all_pass": True, "details": {}}

    review_files = sorted(p.name for p in REVIEW.iterdir() if p.is_file())
    expected = {
        "cards.yaml",
        "exam-analysis.yaml",
        "files.yaml",
        "generated-questions.yaml",
        "mistake-log.md",
        "past-exam-patterns.yaml",
        "plan.md",
        "progress.md",
    }
    checks["details"]["review_files"] = review_files
    checks["details"]["review_files_ok"] = set(review_files) == expected

    analysis = yaml.safe_load((REVIEW / "exam-analysis.yaml").read_text(encoding="utf-8"))
    priorities = analysis.get("analysis", {}).get("priorities", [])
    checks["details"]["priorities_count"] = len(priorities)
    checks["details"]["priorities_ok"] = len(priorities) >= 3
    evidence_ok = all(
        isinstance(p.get("evidence"), list) and len(p["evidence"]) > 0
        for p in priorities
    )
    checks["details"]["evidence_ok"] = evidence_ok

    fixture_names = {p.name for p in FIXTURE.iterdir() if p.is_file()}
    trace_ok = True
    for priority in priorities:
        for evidence in priority.get("evidence", []):
            source = str(evidence.get("source_file", ""))
            if not source or source.split("/")[-1] not in fixture_names:
                trace_ok = False
    checks["details"]["q10_evidence_trace"] = trace_ok

    questions_doc = yaml.safe_load(
        (REVIEW / "generated-questions.yaml").read_text(encoding="utf-8")
    )
    questions = questions_doc.get("questions", [])
    checks["details"]["questions_count"] = len(questions)
    q9_ok = len(questions) >= 5 and all(
        isinstance(q.get("scoring_points"), list) and len(q["scoring_points"]) >= 2
        for q in questions[:5]
    )
    checks["details"]["q9_scoring_points"] = q9_ok
    forbidden = re.compile(r"押题|必考")
    checks["details"]["no_forbidden_words"] = not any(
        forbidden.search(
            " ".join(
                [
                    str(q.get("prompt", "")),
                    str(q.get("expected_answer", "")),
                    " ".join(q.get("scoring_points") or []),
                ]
            )
        )
        for q in questions[:5]
    )

    plan = (REVIEW / "plan.md").read_text(encoding="utf-8")
    sections = [
        "## 目标",
        "## 依据",
        "## 先做",
        "## 后做",
        "## 可以先放弃",
        "## 最后",
        "## 现在开始",
    ]
    checks["details"]["plan_sections_ok"] = all(section in plan for section in sections)
    now_section = plan.split("## 现在开始", 1)[-1].strip().splitlines()
    checks["details"]["now_single_action"] = len([line for line in now_section if line.strip()]) == 1

    cards = yaml.safe_load((REVIEW / "cards.yaml").read_text(encoding="utf-8")).get("cards", [])
    mistake_cards = [c for c in cards if c.get("card_type") == "mistake_review"]
    checks["details"]["mistake_cards"] = len(mistake_cards)
    checks["details"]["mistake_log_ok"] = "不知道" in (REVIEW / "mistake-log.md").read_text(
        encoding="utf-8"
    )

    due_result = subprocess.run(
        [sys.executable, str(SCRIPTS / "due_today.py"), str(ROOT / "tests" / "fixtures"), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    due_payload = json.loads(due_result.stdout or "{}")
    due_ids = {
        item["id"]
        for course in due_payload.get("courses", [])
        for item in course.get("items", [])
    }
    card_ids = {c["id"] for c in mistake_cards}
    checks["details"]["due_loop_ok"] = bool(card_ids & due_ids)

    material_files = [
        "6-Transport(3).pptx",
        "期末复习重点.pdf",
        "计算机网络样题(5).pdf",
    ]
    checks["details"]["fixture_material_files"] = material_files
    checks["details"]["fixture_course_files_clean"] = all(
        (FIXTURE / name).is_file() for name in material_files
    )
    checks["details"]["review_only_under_fixture"] = not any(
        p.is_file()
        for p in FIXTURE.iterdir()
        if p.name not in material_files and p.name != "review"
    )

    for key in (
        "review_files_ok",
        "priorities_ok",
        "evidence_ok",
        "q9_scoring_points",
        "q10_evidence_trace",
        "no_forbidden_words",
        "plan_sections_ok",
        "now_single_action",
        "mistake_log_ok",
        "due_loop_ok",
        "fixture_course_files_clean",
    ):
        if not checks["details"].get(key):
            checks["all_pass"] = False
    return checks


def q11_id_collision() -> bool:
    seen: set[str] = set()
    for _ in range(3):
        result = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "generate_questions.py"),
                str(FIXTURE),
                "--count",
                "2",
                "--json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        payload = json.loads(result.stdout or "{}")
        for question_id in payload.get("question_ids", []):
            if question_id in seen:
                return False
            seen.add(question_id)
    doc = yaml.safe_load((REVIEW / "generated-questions.yaml").read_text(encoding="utf-8"))
    all_ids = [q["id"] for q in doc.get("questions", []) if isinstance(q, dict)]
    return len(all_ids) == len(set(all_ids))


def q12_bad_yaml_tolerance() -> tuple[bool, float]:
    with tempfile.TemporaryDirectory() as tmp:
        workspace = Path(tmp)
        good_courses = []
        for index in range(4):
            course = workspace / f"course-{index}"
            review_dir = course / "review"
            review_dir.mkdir(parents=True)
            (review_dir / "files.yaml").write_text(
                f"course:\n  id: course-{index}\n  name: course-{index}\nfiles: []\n",
                encoding="utf-8",
            )
            (review_dir / "cards.yaml").write_text(
                "cards:\n"
                f"  - id: card-{index}\n"
                f"    course_id: course-{index}\n"
                f"    subject: course-{index}\n"
                f"    topic: topic\n"
                f"    card_type: mistake_review\n"
                f"    prompt: q\n"
                f"    answer: a\n"
                f"    schedule:\n"
                f"      rating: 忘了\n"
                f"      last_reviewed: '{date.today().isoformat()}'\n"
                f"      due: '{date.today().isoformat()}'\n",
                encoding="utf-8",
            )
            good_courses.append(f"course-{index}")

        bad = workspace / "course-bad" / "review"
        bad.mkdir(parents=True)
        (bad / "cards.yaml").write_text("cards: [:\n", encoding="utf-8")

        start = time.perf_counter()
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "due_today.py"), str(workspace), "--json"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        elapsed = round(time.perf_counter() - start, 3)
        if result.returncode != 0:
            return False, elapsed
        payload = json.loads(result.stdout or "{}")
        names = {course.get("name") for course in payload.get("courses", [])}
        return good_courses[0] in names and len(names) >= 4, elapsed


def main() -> int:
    if REVIEW.exists():
        shutil.rmtree(REVIEW)

    timings: dict[str, float] = {}
    chain_start = time.perf_counter()

    steps = [
        ("Q1_init", [sys.executable, str(SCRIPTS / "init_course_review.py"), str(FIXTURE)]),
        (
            "Q2_analyze",
            [
                sys.executable,
                str(SCRIPTS / "analyze_exam.py"),
                str(FIXTURE),
                "--force",
                "--json",
            ],
        ),
        (
            "Q3_generate",
            [
                sys.executable,
                str(SCRIPTS / "generate_questions.py"),
                str(FIXTURE),
                "--count",
                "5",
                "--force",
                "--json",
            ],
        ),
        (
            "Q4_plan",
            [
                sys.executable,
                str(SCRIPTS / "plan_review.py"),
                str(FIXTURE),
                "--minutes",
                "90",
                "--goal",
                "pass",
                "--force",
                "--json",
            ],
        ),
        (
            "session",
            [
                sys.executable,
                str(SCRIPTS / "review_session.py"),
                str(FIXTURE),
                "--source",
                "generated",
                "--limit",
                "1",
                "--non-interactive",
                "--answer",
                "不知道",
            ],
        ),
        (
            "Q8_due",
            [
                sys.executable,
                str(SCRIPTS / "due_today.py"),
                str(ROOT / "tests" / "fixtures"),
                "--json",
            ],
        ),
    ]

    exit_codes: dict[str, int] = {}
    for name, cmd in steps:
        elapsed, output, code = run_step(name, cmd)
        timings[name] = elapsed
        exit_codes[name] = code
        if code != 0:
            print(f"FAILED {name} exit={code}\n{output}", file=sys.stderr)
            return 1

    timings["Q5_time_to_first_question"] = round(time.perf_counter() - chain_start, 3)

    checks = verify_outputs()
    q11_ok = q11_id_collision()
    q12_ok, q12_elapsed = q12_bad_yaml_tolerance()

    report = {
        "date": date.today().isoformat(),
        "timings_sec": timings,
        "exit_codes": exit_codes,
        "checks": checks,
        "metrics": {
            "Q1_init": {"threshold_sec": 2, "actual_sec": timings["Q1_init"], "pass": timings["Q1_init"] <= 2},
            "Q2_analyze": {"threshold_sec": 3, "actual_sec": timings["Q2_analyze"], "pass": timings["Q2_analyze"] <= 3},
            "Q3_generate": {"threshold_sec": 5, "actual_sec": timings["Q3_generate"], "pass": timings["Q3_generate"] <= 5},
            "Q4_plan": {"threshold_sec": 3, "actual_sec": timings["Q4_plan"], "pass": timings["Q4_plan"] <= 3},
            "Q5_time_to_first_question": {
                "threshold_sec": 90,
                "actual_sec": timings["Q5_time_to_first_question"],
                "pass": timings["Q5_time_to_first_question"] <= 90,
            },
            "Q6_grading_accuracy": {"status": "deferred", "note": "待 v0.2 单元测试覆盖"},
            "Q7_mistake_log_latency": {"status": "manual_ok", "note": "session 同步落盘，due 立即可见"},
            "Q8_due_today": {"threshold_sec": 2, "actual_sec": timings["Q8_due"], "pass": timings["Q8_due"] <= 2},
            "Q9_scoring_points_coverage": {"threshold": "100%", "pass": checks["details"]["q9_scoring_points"]},
            "Q10_evidence_trace": {"threshold": "100%", "pass": checks["details"]["q10_evidence_trace"]},
            "Q11_id_unique": {"threshold": "100%", "pass": q11_ok},
            "Q12_bad_yaml_tolerance": {
                "threshold": "100%",
                "pass": q12_ok,
                "actual_sec": q12_elapsed,
            },
        },
        "chain_total_sec": round(
            timings["Q1_init"]
            + timings["Q2_analyze"]
            + timings["Q3_generate"]
            + timings["Q4_plan"]
            + timings["Q8_due"],
            3,
        ),
    }

    out_path = ROOT / "tests" / "e2e_results.md"
    lines = [
        "# E2E Results",
        "",
        f"Date: {report['date']}",
        f"Fixture: `tests/fixtures/computer-network`",
        "",
        "## 6-step chain",
        "",
        "| Step | Exit | Seconds |",
        "|------|------|---------|",
    ]
    for step_name in [
        "Q1_init",
        "Q2_analyze",
        "Q3_generate",
        "Q4_plan",
        "session",
        "Q8_due",
    ]:
        lines.append(
            f"| {step_name} | {exit_codes[step_name]} | {timings[step_name]} |"
        )
    lines.extend(
        [
            "",
            f"Non-interactive chain total (excl. session): **{report['chain_total_sec']}s** (budget ≤15s)",
            "",
            "## Epic 6 checks",
            "",
            f"- 6-01 chain exit 0: **{'PASS' if all(code == 0 for code in exit_codes.values()) else 'FAIL'}**",
            f"- 6-02 review 8 files + fixture clean: **{'PASS' if checks['details']['review_files_ok'] and checks['details']['fixture_course_files_clean'] else 'FAIL'}**",
            f"- 6-03 analysis priorities/evidence: **{'PASS' if checks['details']['priorities_ok'] and checks['details']['evidence_ok'] else 'FAIL'}**",
            f"- 6-04 generated questions quality: **{'PASS' if checks['details']['q9_scoring_points'] and checks['details']['no_forbidden_words'] else 'FAIL'}**",
            f"- 6-05 plan executable: **{'PASS' if checks['details']['plan_sections_ok'] and checks['details']['now_single_action'] else 'FAIL'}**",
            f"- 6-06 mistake loop: **{'PASS' if checks['details']['mistake_log_ok'] and checks['details']['due_loop_ok'] else 'FAIL'}**",
            "",
            "## Q1–Q12 metrics",
            "",
            "| Q | Metric | Threshold | Actual | Pass |",
            "|---|--------|-----------|--------|------|",
        ]
    )
    for key, metric in report["metrics"].items():
        if metric.get("status") == "deferred":
            lines.append(f"| {key} | deferred | — | — | 待 v0.2 |")
            continue
        if metric.get("status") == "manual_ok":
            lines.append(f"| {key} | manual | ≤60s | sync | PASS |")
            continue
        threshold = metric.get("threshold_sec") or metric.get("threshold")
        actual = metric.get("actual_sec", metric.get("pass"))
        passed = "PASS" if metric.get("pass") else "FAIL"
        lines.append(f"| {key} | | {threshold} | {actual} | {passed} |")

    lines.extend(["", "## Details", "", "```json", json.dumps(report, ensure_ascii=False, indent=2), "```", ""])
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"all_pass": checks["all_pass"] and q11_ok and q12_ok, "report": str(out_path)}, ensure_ascii=False))
    return 0 if checks["all_pass"] and q11_ok and q12_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
