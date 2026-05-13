from __future__ import annotations

import ast
import re
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Any


FINDING_WEIGHTS = {
    "critical": 30,
    "high": 22,
    "medium": 12,
    "low": 6,
}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _line_count(content: str) -> int:
    return len([line for line in content.splitlines() if line.strip()])


class DataEngineerSkillPack:
    """
    Local deterministic skill pack for data-engineering work.
    The goal is not to replace a senior engineer; it gives Omni grounded
    rubrics and task scores without needing web access or model inference.
    """

    template_id = "data_engineer"

    def definition(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": "Data Engineer",
            "version": "0.2.0",
            "artifact_types": ["sql_model", "dbt_yaml", "airflow_dag", "runbook"],
            "tools": ["sql", "dbt", "airflow", "spark", "warehouse", "lineage", "git"],
            "task_rubrics": [
                "SQL grain, joins, incremental safety, and performance",
                "dbt tests, source freshness, contracts, and ownership",
                "Airflow retry, schedule, alerting, backfill, and failure recovery",
                "Runbook clarity, rollback, validation, communication, and escalation",
            ],
        }

    def review_artifact(self, artifact_path: str | Path, workspace_root: str | Path | None = None) -> dict:
        path = Path(artifact_path).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"Artifact path does not exist: {path}")
        if path.is_dir():
            raise IsADirectoryError(f"Artifact review expects a file, got directory: {path}")

        content = path.read_text(encoding="utf-8", errors="ignore")
        root = Path(workspace_root).expanduser().resolve() if workspace_root else path.parent
        try:
            relative_path = str(path.relative_to(root))
        except ValueError:
            relative_path = str(path)

        suffix = path.suffix.lower()
        if suffix == ".sql":
            review = self._review_sql(path, content)
        elif suffix in {".yml", ".yaml"}:
            review = self._review_yaml(path, content)
        elif suffix == ".py":
            review = self._review_python(path, content)
        elif suffix in {".md", ".txt"}:
            review = self._review_runbook(path, content)
        else:
            review = self._review_generic(path, content)

        score = self._score(review["findings"])
        review.update(
            {
                "id": str(uuid.uuid4()),
                "path": relative_path,
                "absolute_path": str(path),
                "score": score,
                "grade": self._grade(score),
                "created_at": time.time(),
                "summary": self._summary(review["artifact_type"], score, review["findings"], review["strengths"]),
            }
        )
        return review

    def evaluate_workspace(self, snapshot: dict | None) -> dict:
        if not snapshot:
            return {
                "status": "unconfigured",
                "overall_score": 0.0,
                "tasks": [],
                "summary": "No workspace snapshot is available for data-engineering evaluation.",
            }

        workspace_path = Path(snapshot.get("workspace_path", "")).expanduser()
        task_groups = {
            "SQL Model Review": ["sql_model"],
            "dbt Quality Coverage": ["config"],
            "Airflow Recovery": ["python_job"],
            "Operator Runbook": ["document"],
        }
        grouped_reviews: dict[str, list[dict]] = {name: [] for name in task_groups}

        for artifact in snapshot.get("artifacts", []):
            path = workspace_path / artifact.get("path", "")
            if not path.exists():
                continue
            try:
                review = self.review_artifact(path, workspace_root=workspace_path)
            except Exception:
                continue
            for task_name, kinds in task_groups.items():
                if artifact.get("kind") in kinds:
                    grouped_reviews[task_name].append(review)

        tasks = []
        for task_name, reviews in grouped_reviews.items():
            if not reviews:
                tasks.append(
                    {
                        "name": task_name,
                        "status": "missing_evidence",
                        "score": 0.0,
                        "evidence": [],
                        "next_step": self._missing_task_step(task_name),
                    }
                )
                continue
            avg_score = round(sum(review["score"] for review in reviews) / len(reviews), 2)
            high_findings = [
                finding
                for review in reviews
                for finding in review.get("findings", [])
                if finding.get("severity") in {"critical", "high"}
            ]
            tasks.append(
                {
                    "name": task_name,
                    "status": "ready" if avg_score >= 75 and not high_findings else "needs_work",
                    "score": avg_score,
                    "evidence": [review["path"] for review in reviews],
                    "top_findings": high_findings[:3],
                    "next_step": high_findings[0]["recommendation"] if high_findings else "Use this task on live work and capture feedback.",
                }
            )

        overall = round(sum(task["score"] for task in tasks) / max(len(tasks), 1), 2)
        return {
            "status": "ready" if overall >= 80 and all(task["status"] == "ready" for task in tasks) else "training",
            "overall_score": overall,
            "tasks": tasks,
            "summary": f"Data-engineering task evaluation scored {overall:.2f} across {len(tasks)} rubric areas.",
            "created_at": time.time(),
        }

    def _review_sql(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        findings = []
        strengths = []
        metrics = {
            "lines": _line_count(content),
            "joins": len(re.findall(r"\bjoin\b", lowered)),
            "ctes": len(re.findall(r"\bwith\s+[a-zA-Z_]", lowered)),
            "windows": len(re.findall(r"\bover\s*\(", lowered)),
            "aggregations": len(re.findall(r"\b(sum|count|avg|min|max)\s*\(", lowered)),
            "has_where": bool(re.search(r"\bwhere\b", lowered)),
            "has_group_by": bool(re.search(r"\bgroup\s+by\b", lowered)),
            "has_incremental_logic": any(token in lowered for token in ["is_incremental", "merge into", "incremental", "unique_key", "watermark"]),
            "has_quality_terms": any(token in lowered for token in ["not null", "unique", "accepted_values", "relationships", "test"]),
        }

        if re.search(r"select\s+\*", lowered):
            findings.append(self._finding("high", "Avoid select star", "The model selects all columns, which hides schema drift and lineage impact.", "Select named columns and document grain.", "SQL Modeling"))
        else:
            strengths.append("Uses explicit projection instead of select star.")

        if metrics["aggregations"] and not metrics["has_group_by"]:
            findings.append(self._finding("high", "Aggregation grain is unclear", "The query aggregates without an explicit group by.", "Define the output grain and group by stable keys.", "SQL Modeling"))
        elif metrics["aggregations"]:
            strengths.append("Aggregations include an explicit grouping pattern.")

        if metrics["joins"] and not metrics["has_quality_terms"]:
            findings.append(self._finding("medium", "Join assumptions need tests", "The model joins datasets without nearby uniqueness or relationship signals.", "Add dbt relationship and uniqueness tests for join keys.", "Data Quality"))
        elif metrics["joins"]:
            strengths.append("Join-heavy logic has some quality signals.")

        if metrics["has_incremental_logic"] and not any(token in lowered for token in ["unique_key", "merge", "watermark", "updated_at"]):
            findings.append(self._finding("high", "Incremental safety is incomplete", "Incremental intent appears without a clear merge key or watermark.", "Declare unique_key and late-arriving data handling.", "Performance"))

        if metrics["lines"] > 80 and not re.search(r"--|/\*", content):
            findings.append(self._finding("low", "Complex model needs commentary", "The model is long but has no explanatory comments.", "Add comments around grain, filters, and business rules.", "Communication"))

        if not metrics["has_where"] and metrics["lines"] > 12:
            findings.append(self._finding("medium", "No pruning filter found", "The model has enough logic to justify checking scan volume, but no where clause was detected.", "Add partition pruning or document why full scans are acceptable.", "Performance"))

        if not findings:
            strengths.append("No obvious SQL modeling risks detected by local rubric.")

        return {
            "artifact_type": "sql_model",
            "metrics": metrics,
            "findings": findings,
            "strengths": strengths,
            "suggested_tests": self._suggest_sql_tests(path, lowered, metrics),
        }

    def _review_yaml(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        findings = []
        strengths = []
        test_count = len(re.findall(r"\b(not_null|unique|relationships|accepted_values|tests:|data_tests:)\b", lowered))
        model_count = len(re.findall(r"^\s*-\s+name:", content, flags=re.MULTILINE))
        has_sources = "sources:" in lowered
        has_freshness = "freshness:" in lowered or "loaded_at_field:" in lowered
        has_owner = "owner:" in lowered or "meta:" in lowered

        if model_count and test_count == 0:
            findings.append(self._finding("high", "dbt models lack tests", "Model metadata exists but no quality tests were detected.", "Add not_null, unique, accepted_values, and relationship tests around grain and joins.", "Data Quality"))
        elif test_count:
            strengths.append(f"Detected {test_count} dbt quality test signal(s).")

        if has_sources and not has_freshness:
            findings.append(self._finding("medium", "Source freshness missing", "Sources are declared without freshness or loaded_at metadata.", "Add source freshness checks for upstream reliability.", "Incident Response"))
        elif has_sources:
            strengths.append("Source metadata includes freshness-style signals.")

        if not has_owner:
            findings.append(self._finding("low", "Ownership metadata missing", "No owner or meta field was detected.", "Add owner metadata so incidents route to the right human.", "Communication"))

        return {
            "artifact_type": "dbt_yaml",
            "metrics": {
                "models": model_count,
                "test_signals": test_count,
                "has_sources": has_sources,
                "has_freshness": has_freshness,
                "has_owner": has_owner,
            },
            "findings": findings,
            "strengths": strengths or ["YAML artifact is readable and carries dbt-style metadata."],
            "suggested_tests": ["Add model-level not_null and unique tests for declared grain."] if test_count == 0 else [],
        }

    def _review_python(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        findings = []
        strengths = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            tree = None

        metrics = {
            "is_airflow": any(token in lowered for token in ["from airflow", "airflow.", "dag(", "@dag"]),
            "operators": len(re.findall(r"(pythonoperator|bashoperator|sqloperator|sparksubmitoperator|operator\()", lowered)),
            "has_retries": "retries" in lowered or "retry_delay" in lowered,
            "has_failure_callback": "on_failure_callback" in lowered or "sla_miss_callback" in lowered,
            "has_schedule": "schedule_interval" in lowered or "schedule=" in lowered,
            "catchup_false": "catchup=false" in lowered.replace(" ", ""),
            "function_count": len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]) if tree else 0,
        }

        if metrics["is_airflow"]:
            strengths.append("Detected Airflow DAG patterns.")
            if not metrics["has_retries"]:
                findings.append(self._finding("high", "Retries are not explicit", "The DAG does not show retry policy.", "Set retries and retry_delay in default_args or task config.", "Orchestration"))
            if not metrics["has_failure_callback"]:
                findings.append(self._finding("medium", "Failure callback missing", "No alerting or failure callback was detected.", "Add alerting with on_failure_callback or a platform-native notification path.", "Incident Response"))
            if not metrics["has_schedule"]:
                findings.append(self._finding("medium", "Schedule is unclear", "The DAG schedule was not detected.", "Declare schedule and document expected data availability.", "Orchestration"))
            if not metrics["catchup_false"]:
                findings.append(self._finding("low", "Catchup policy needs review", "No explicit catchup=False signal was detected.", "Declare catchup behavior and backfill policy.", "Incident Response"))
        else:
            findings.append(self._finding("medium", "Python job is not classified", "The file does not show Airflow, Spark, or validation patterns.", "Document how this job runs, retries, and reports failure.", "Communication"))

        return {
            "artifact_type": "airflow_dag" if metrics["is_airflow"] else "python_job",
            "metrics": metrics,
            "findings": findings,
            "strengths": strengths or ["Python artifact parsed successfully."],
            "suggested_tests": ["Add a DAG import test and a task dependency smoke test."] if metrics["is_airflow"] else [],
        }

    def _review_runbook(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        headings = len(re.findall(r"^#+\s+", content, flags=re.MULTILINE))
        checks = {
            "rollback": any(token in lowered for token in ["rollback", "revert", "restore"]),
            "telemetry": any(token in lowered for token in ["log", "metric", "dashboard", "alert", "trace"]),
            "validation": any(token in lowered for token in ["validate", "verify", "check", "test"]),
            "escalation": any(token in lowered for token in ["owner", "escalate", "severity", "slack", "pager"]),
            "backfill": "backfill" in lowered,
        }
        findings = []
        for key, present in checks.items():
            if present:
                continue
            findings.append(self._finding("medium" if key in {"rollback", "validation"} else "low", f"Runbook missing {key}", f"No {key} instruction was detected.", f"Add a clear {key} step for operators.", "Incident Response"))

        return {
            "artifact_type": "runbook",
            "metrics": {"headings": headings, **checks},
            "findings": findings,
            "strengths": [f"Runbook includes {key} guidance." for key, present in checks.items() if present] or ["Runbook text is available for operator review."],
            "suggested_tests": ["Dry-run the runbook against a simulated incident and capture missing steps."],
        }

    def _review_generic(self, path: Path, content: str) -> dict:
        return {
            "artifact_type": "document",
            "metrics": {"lines": _line_count(content)},
            "findings": [self._finding("low", "Generic artifact", "This file is not a first-class data-engineering artifact yet.", "Add a specific parser or classify it manually.", "Domain Knowledge")],
            "strengths": ["Artifact is available for local memory."],
            "suggested_tests": [],
        }

    def _finding(self, severity: str, title: str, detail: str, recommendation: str, competency: str) -> dict:
        return {
            "severity": severity,
            "title": title,
            "detail": detail,
            "recommendation": recommendation,
            "competency": competency,
        }

    def _score(self, findings: list[dict]) -> float:
        penalty = sum(FINDING_WEIGHTS.get(finding.get("severity", "low"), 6) for finding in findings)
        return round(max(0.0, 100.0 - penalty), 2)

    def _grade(self, score: float) -> str:
        if score >= 90:
            return "excellent"
        if score >= 75:
            return "strong"
        if score >= 60:
            return "needs_review"
        return "high_risk"

    def _summary(self, artifact_type: str, score: float, findings: list[dict], strengths: list[str]) -> str:
        if findings:
            counts = Counter(finding["severity"] for finding in findings)
            finding_text = ", ".join(f"{count} {severity}" for severity, count in counts.items())
            return f"{artifact_type.replace('_', ' ').title()} scored {score:.0f} with {finding_text} finding(s)."
        return f"{artifact_type.replace('_', ' ').title()} scored {score:.0f}. {strengths[0] if strengths else 'No obvious issues detected.'}"

    def _suggest_sql_tests(self, path: Path, lowered: str, metrics: dict) -> list[str]:
        suggestions = []
        if metrics["joins"]:
            suggestions.append("Add relationship tests for join keys.")
        if metrics["aggregations"]:
            suggestions.append("Add uniqueness tests for the declared output grain.")
        if "customer" in lowered:
            suggestions.append("Add not_null tests for customer identifiers.")
        if "order" in lowered or "date" in lowered:
            suggestions.append("Add freshness or accepted range checks for date fields.")
        return suggestions[:4]

    def _missing_task_step(self, task_name: str) -> str:
        return {
            "SQL Model Review": "Import at least one SQL model.",
            "dbt Quality Coverage": "Import dbt schema YAML with model and source tests.",
            "Airflow Recovery": "Import an Airflow DAG or orchestration file.",
            "Operator Runbook": "Import incident runbooks or postmortems.",
        }.get(task_name, "Import more local evidence.")
