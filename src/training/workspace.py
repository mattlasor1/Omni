from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable

from src.training.personal_twin import PersonalTwinLearningPack


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
    ".csv",
    ".ini",
    ".js",
    ".jsx",
    ".json",
    ".md",
    ".py",
    ".rst",
    ".sql",
    ".toml",
    ".ts",
    ".tsx",
    ".tsv",
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
        learning_pack = PersonalTwinLearningPack()

        for file_path in candidates[:max_files]:
            artifact = self._inspect_file(file_path)
            if not artifact:
                continue
            artifact = self._attach_adaptation_review(artifact, file_path, learning_pack)
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
            "adaptation_model": learning_pack.definition(),
            "competency_signal": self._build_competency_signal(profile, skill_counter),
            "evaluation_scenarios": self._build_evaluation_scenarios(profile, artifacts, frameworks),
            "recommended_next_steps": self._build_next_steps(artifacts, frameworks, skill_counter),
        }
        return report

    def _attach_adaptation_review(self, artifact: dict, path: Path, learning_pack: PersonalTwinLearningPack) -> dict:
        try:
            review = learning_pack.review_artifact(path, workspace_root=self.root if self.root.is_dir() else path.parent)
        except Exception:
            return artifact
        return {
            **artifact,
            "review_score": review["score"],
            "review_grade": review["grade"],
            "finding_count": len(review.get("findings", [])),
            "review_findings": review.get("findings", [])[:3],
            "suggested_tests": review.get("suggested_tests", [])[:4],
        }

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

        suffix = path.suffix.lower()
        skill_tags.add("domain_understanding")
        if suffix == ".sql":
            kind = "query"
            frameworks.add("query")
            skill_tags.add("artifact_fluency")
            signals.append("Contains a structured query artifact.")
        elif suffix in {".yml", ".yaml", ".json", ".toml", ".ini", ".cfg"}:
            kind = "config"
            frameworks.add(suffix.lstrip("."))
            skill_tags.add("artifact_fluency")
            signals.append("Contains configuration or metadata.")
        elif suffix in {".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java", ".cs"}:
            kind = "code"
            frameworks.add(self._language_for_suffix(suffix))
            skill_tags.update({"artifact_fluency", "workflow_fluency"})
            signals.append("Contains executable or automation logic.")
        elif suffix in {".csv", ".tsv"}:
            kind = "data_sample"
            frameworks.add("structured_data")
            skill_tags.update({"artifact_fluency", "domain_understanding"})
            signals.append("Contains a structured data sample.")
        else:
            kind = "document"
            skill_tags.add("communication_style")
            signals.append("Contains written context for local learning.")

        if any(token in lowered for token in ["goal", "preference", "style", "tone", "constraint", "value"]):
            skill_tags.add("owner_identity")
            signals.append("Carries owner identity or preference hints.")
        if any(token in lowered for token in ["workflow", "process", "step", "procedure", "runbook", "checklist", "handoff", "schedule"]):
            skill_tags.add("workflow_fluency")
            signals.append("Describes repeatable work or procedure.")
        if any(token in lowered for token in ["decision", "tradeoff", "risk", "criteria", "standard", "quality", "acceptance"]):
            skill_tags.add("decision_judgment")
            signals.append("Carries decision criteria or quality standards.")
        if any(token in lowered for token in ["validate", "verify", "test", "assert", "expected", "success"]):
            skill_tags.add("quality_standards")
            signals.append("Contains validation or success signals.")
        if any(token in lowered for token in ["feedback", "correction", "prefer", "instead", "wrong", "self-review"]):
            skill_tags.add("feedback_adaptation")
            signals.append("Contains feedback or correction signals.")

        if not skill_tags and not frameworks and suffix not in {".md", ".txt", ".rst"}:
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

    def _language_for_suffix(self, suffix: str) -> str:
        return {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".rs": "rust",
            ".go": "go",
            ".java": "java",
            ".cs": "csharp",
        }.get(suffix, suffix.lstrip("."))

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
            return "No supported owner-model artifacts were detected in the selected path."
        kinds = Counter(artifact["kind"] for artifact in artifacts)
        top_kinds = ", ".join(f"{count} {kind.replace('_', ' ')}" for kind, count in kinds.most_common(3))
        framework_phrase = ", ".join(sorted(frameworks)) if frameworks else "custom local patterns"
        return f"Detected {len(artifacts)} useful owner-model artifacts across {top_kinds}. Dominant local tools and conventions: {framework_phrase}."

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
        doc_artifact = artifact_lookup.get("document")
        code_artifact = artifact_lookup.get("code") or artifact_lookup.get("query")
        scenarios.append(
            {
                "name": "Owner Context Recall",
                "goal": "Summarize the owner's goals, constraints, vocabulary, and preferred working style from local evidence.",
                "competencies": ["Owner Identity", "Domain Understanding"],
            }
        )
        scenarios.append(
            {
                "name": "Workflow Reconstruction",
                "goal": f"Explain the repeatable workflow implied by {doc_artifact['path']} and name the checks that matter." if doc_artifact else "Reconstruct a recurring owner workflow from imported artifacts and lessons.",
                "competencies": ["Workflow Fluency", "Quality Standards"],
            }
        )
        scenarios.append(
            {
                "name": "Artifact Application",
                "goal": f"Review {code_artifact['path']} through the owner's standards and suggest the next safest action." if code_artifact else "Apply the owner's standards to a local artifact and recommend a grounded next action.",
                "competencies": ["Artifact Fluency", "Decision Judgment"],
            }
        )
        scenarios.append(
            {
                "name": "Feedback Alignment",
                "goal": "Use recent corrections and lessons to adjust the response style and decision criteria.",
                "competencies": ["Feedback Adaptation", "Communication Style"],
            }
        )
        return scenarios

    def _build_next_steps(self, artifacts: list[dict], frameworks: set[str], skill_counter: Counter) -> list[str]:
        next_steps = []
        if not artifacts:
            next_steps.append("Point Omni at a folder with local notes, decisions, examples, code, configs, or workflow artifacts.")
            return next_steps
        if skill_counter.get("owner_identity", 0) == 0:
            next_steps.append("Add notes about your goals, constraints, preferences, values, and communication style.")
        if skill_counter.get("workflow_fluency", 0) == 0:
            next_steps.append("Add examples of recurring workflows, procedures, handoffs, and recovery paths.")
        if skill_counter.get("decision_judgment", 0) == 0:
            next_steps.append("Add decision notes that show criteria, tradeoffs, risk tolerance, and quality standards.")
        if skill_counter.get("feedback_adaptation", 0) == 0:
            next_steps.append("Correct Omni during real use and store those corrections as feedback lessons.")
        if not next_steps:
            next_steps.append("Import this workspace into training, then run owner-model evaluations against live tasks.")
        return next_steps
