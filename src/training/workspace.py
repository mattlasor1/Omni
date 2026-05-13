from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable


IGNORED_DIRS = {
    ".git",
    ".next",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "target",
    "venv",
}
SUPPORTED_EXTENSIONS = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".py",
    ".sql",
    ".txt",
    ".yaml",
    ".yml",
}
MAX_FILE_SIZE = 200_000


def _clean_line(line: str) -> str:
    return re.sub(r"\s+", " ", line.strip())


def _first_meaningful_lines(content: str, limit: int = 3) -> list[str]:
    lines = [_clean_line(line) for line in content.splitlines()]
    return [line for line in lines if line][:limit]


class WorkspaceAnalyzer:
    def __init__(self, root_path: str):
        self.root = Path(root_path).expanduser().resolve()

    def analyze(self, profile: dict | None = None, max_files: int = 200) -> dict:
        if not self.root.exists():
            raise FileNotFoundError(f"Workspace path does not exist: {self.root}")

        candidates = list(self._iter_candidate_files())
        artifacts = []
        frameworks = set()
        skill_counter = Counter()
        kind_counter = Counter()

        for file_path in candidates[:max_files]:
            artifact = self._inspect_file(file_path)
            if not artifact:
                continue
            artifacts.append(artifact)
            frameworks.update(artifact["frameworks"])
            skill_counter.update(artifact["skill_tags"])
            kind_counter.update([artifact["kind"]])

        report = {
            "workspace_path": str(self.root),
            "workspace_name": self.root.name,
            "selected_files": len(artifacts),
            "frameworks": sorted(frameworks),
            "artifact_counts": dict(kind_counter),
            "skill_signals": dict(skill_counter),
            "artifacts": artifacts[:30],
            "summary": self._build_summary(artifacts, frameworks),
            "competency_signal": self._build_competency_signal(profile, skill_counter),
            "evaluation_scenarios": self._build_evaluation_scenarios(profile, artifacts, frameworks),
            "recommended_next_steps": self._build_next_steps(artifacts, frameworks, skill_counter),
        }
        return report

    def _iter_candidate_files(self) -> Iterable[Path]:
        if self.root.is_file():
            if self.root.suffix.lower() in SUPPORTED_EXTENSIONS and self.root.stat().st_size <= MAX_FILE_SIZE:
                yield self.root
            return

        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in IGNORED_DIRS for part in path.parts):
                continue
            if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            try:
                if path.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue
            yield path

    def _inspect_file(self, path: Path) -> dict | None:
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None

        lowered = content.lower()
        rel_path = str(path.relative_to(self.root if self.root.is_dir() else path.parent))
        skill_tags: set[str] = set()
        frameworks: set[str] = set()
        signals: list[str] = []
        kind = "document"

        if path.suffix.lower() == ".sql":
            kind = "sql_model"
            skill_tags.add("sql_modeling")
            if " join " in lowered:
                signals.append("Uses explicit joins.")
            if any(token in lowered for token in ["partition by", "cluster by", "incremental", "merge into", "is_incremental"]):
                skill_tags.add("performance")
                signals.append("Contains performance-aware SQL patterns.")
            if any(token in lowered for token in ["not null", "unique", "accepted_values", "relationships"]):
                skill_tags.add("data_quality")
                signals.append("Embeds data quality constraints or tests.")
            if "models" in {part.lower() for part in path.parts}:
                frameworks.add("dbt")
                signals.append("Lives in a dbt-style models directory.")
        elif path.suffix.lower() in {".yml", ".yaml"}:
            kind = "config"
            if "dbt_project" in path.name.lower() or "models:" in lowered or "sources:" in lowered:
                frameworks.add("dbt")
                skill_tags.update({"sql_modeling", "data_quality"})
                signals.append("Defines dbt project or model metadata.")
            if any(token in lowered for token in ["freshness", "tests:", "not_null", "unique"]):
                skill_tags.add("data_quality")
                signals.append("Declares data tests or freshness checks.")
            if any(token in lowered for token in ["owner:", "schedule:", "retries:", "sla:"]):
                skill_tags.add("orchestration")
                signals.append("Carries operational scheduling or ownership hints.")
        elif path.suffix.lower() == ".py":
            kind = "python_job"
            if any(token in lowered for token in ["from airflow", "airflow.", "dag(", "@dag", "pythonoperator", "bashoperator"]):
                frameworks.add("airflow")
                skill_tags.add("orchestration")
                signals.append("Contains Airflow DAG logic.")
            if any(token in lowered for token in ["pyspark", "sparksession", ".write.format(", ".read.format("]):
                frameworks.add("spark")
                skill_tags.add("performance")
                signals.append("Contains Spark-style data processing.")
            if any(token in lowered for token in ["retry", "on_failure_callback", "alert", "pagerduty", "slack"]):
                skill_tags.add("incident_response")
                signals.append("Contains failure handling or alerting logic.")
            if any(token in lowered for token in ["expect_", "great_expectations", "assert "]):
                skill_tags.add("data_quality")
                signals.append("Includes validation or assertion logic.")
        else:
            kind = "document"
            if any(token in lowered for token in ["runbook", "incident", "rollback", "severity", "triage", "postmortem"]):
                skill_tags.update({"incident_response", "communication"})
                signals.append("Reads like an operational runbook.")
            if any(token in lowered for token in ["schema", "contract", "lineage", "source of truth"]):
                skill_tags.update({"data_quality", "communication"})
                signals.append("Documents model expectations or data contracts.")
            if any(token in lowered for token in ["dbt", "sql", "warehouse", "pipeline"]):
                skill_tags.add("sql_modeling")

        if not skill_tags and not frameworks and path.suffix.lower() not in {".md", ".txt"}:
            return None

        preview_lines = _first_meaningful_lines(content)
        summary = self._build_artifact_summary(path.name, kind, skill_tags, signals, preview_lines)

        return {
            "path": rel_path,
            "name": path.name,
            "kind": kind,
            "summary": summary,
            "skill_tags": sorted(skill_tags),
            "frameworks": sorted(frameworks),
            "signals": signals[:4],
            "preview": preview_lines,
        }

    def _build_artifact_summary(
        self,
        name: str,
        kind: str,
        skill_tags: set[str],
        signals: list[str],
        preview_lines: list[str],
    ) -> str:
        skill_phrase = ", ".join(sorted(skill_tags)) if skill_tags else "general domain knowledge"
        signal_phrase = signals[0] if signals else "Provides local implementation detail."
        preview = preview_lines[0] if preview_lines else ""
        pieces = [f"{name} is a {kind.replace('_', ' ')} artifact tied to {skill_phrase}.", signal_phrase]
        if preview:
            pieces.append(f"Preview: {preview}")
        return " ".join(pieces)

    def _build_summary(self, artifacts: list[dict], frameworks: set[str]) -> str:
        if not artifacts:
            return "No supported profession artifacts were detected in the selected path."
        kinds = Counter(artifact["kind"] for artifact in artifacts)
        top_kinds = ", ".join(f"{count} {kind.replace('_', ' ')}" for kind, count in kinds.most_common(3))
        framework_phrase = ", ".join(sorted(frameworks)) if frameworks else "custom local patterns"
        return f"Detected {len(artifacts)} useful artifacts across {top_kinds}. Dominant frameworks and conventions: {framework_phrase}."

    def _build_competency_signal(self, profile: dict | None, skill_counter: Counter) -> list[dict]:
        if not profile:
            return []
        signals = []
        for competency in profile.get("competencies", []):
            matches = sum(count for skill, count in skill_counter.items() if competency["name"] in skill or skill in competency["name"])
            related = [skill for skill in skill_counter if competency["name"].split("_")[0] in skill or skill in competency["name"]]
            signals.append(
                {
                    "competency": competency["label"],
                    "matched_artifacts": matches,
                    "related_skills": sorted(set(related)),
                }
            )
        return signals

    def _build_evaluation_scenarios(self, profile: dict | None, artifacts: list[dict], frameworks: set[str]) -> list[dict]:
        scenarios = []
        if not profile:
            return scenarios

        artifact_lookup = {artifact["kind"]: artifact for artifact in artifacts}
        if profile.get("template_id") == "data_engineer" or profile.get("label") == "Data Engineer":
            sql_artifact = artifact_lookup.get("sql_model")
            dag_artifact = artifact_lookup.get("python_job")
            doc_artifact = artifact_lookup.get("document")
            scenarios.append(
                {
                    "name": "SQL Review",
                    "goal": f"Explain how you would review and improve {sql_artifact['path']} for correctness and maintainability." if sql_artifact else "Review a warehouse SQL model for joins, grain, and incremental safety.",
                    "competencies": ["SQL Modeling", "Performance"],
                }
            )
            scenarios.append(
                {
                    "name": "Orchestration Recovery",
                    "goal": f"Design a failure-response plan for {dag_artifact['path']} and name the first telemetry you would inspect." if dag_artifact else "Recover a failed DAG and explain the retry, alerting, and backfill plan.",
                    "competencies": ["Orchestration", "Incident Response"],
                }
            )
            scenarios.append(
                {
                    "name": "Runbook Clarity",
                    "goal": f"Turn {doc_artifact['path']} into a tighter operator runbook with rollback steps." if doc_artifact else "Write a concise operator runbook for a broken data load.",
                    "competencies": ["Communication", "Incident Response"],
                }
            )
        else:
            scenarios.append(
                {
                    "name": "Domain Recall",
                    "goal": "Summarize the strongest rules, workflows, and risks present in the imported workspace.",
                    "competencies": ["Domain Knowledge", "Workflows"],
                }
            )
        return scenarios

    def _build_next_steps(self, artifacts: list[dict], frameworks: set[str], skill_counter: Counter) -> list[str]:
        next_steps = []
        if not artifacts:
            next_steps.append("Point Omni at a directory with SQL, Python, YAML, or runbook files.")
            return next_steps
        if "dbt" not in frameworks:
            next_steps.append("Add dbt model or schema files if you want deeper warehouse modeling context.")
        if "airflow" not in frameworks:
            next_steps.append("Add DAG or orchestration code so Omni can learn operational flow and recovery patterns.")
        if skill_counter.get("incident_response", 0) == 0:
            next_steps.append("Import incident runbooks or postmortems to strengthen response guidance.")
        if skill_counter.get("data_quality", 0) == 0:
            next_steps.append("Import tests, contracts, or freshness policies to improve data quality reasoning.")
        if not next_steps:
            next_steps.append("Import this workspace into training, then run evaluation scenarios against live tasks.")
        return next_steps
