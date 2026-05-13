from __future__ import annotations

import ast
import csv
import json
import re
import time
import uuid
from collections import Counter
from pathlib import Path
from typing import Iterable


FINDING_WEIGHTS = {
    "critical": 30,
    "high": 22,
    "medium": 12,
    "low": 6,
}

CODE_EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".rs", ".go", ".java", ".cs"}
CONFIG_EXTENSIONS = {".cfg", ".ini", ".json", ".toml", ".yaml", ".yml"}
DOCUMENT_EXTENSIONS = {".md", ".rst", ".txt"}
DATA_EXTENSIONS = {".csv", ".tsv"}
QUERY_EXTENSIONS = {".sql"}


def _clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _line_count(content: str) -> int:
    return len([line for line in content.splitlines() if line.strip()])


def _has_any(text: str, terms: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


class PersonalTwinLearningPack:
    """
    Deterministic owner-adaptation rubric for the offline twin.
    It is intentionally career-neutral: the twin learns the owner's identity,
    standards, domain, workflow, decision habits, and feedback patterns from
    local evidence instead of from a hard-coded job description.
    """

    template_id = "personal_twin"

    def definition(self) -> dict:
        return {
            "template_id": self.template_id,
            "name": "Personal Twin Adaptation",
            "version": "0.3.0",
            "artifact_types": ["document", "code", "config", "query", "data_sample", "workflow_note"],
            "learning_axes": [
                "Owner identity, goals, constraints, values, and communication preferences",
                "Domain vocabulary, tools, artifacts, and operating environment",
                "Repeatable workflows, procedures, handoffs, and failure modes",
                "Decision standards, tradeoffs, risks, and quality bars",
                "Feedback assimilation, corrections, self-review, and behavior refinement",
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

        artifact_type = self._artifact_type(path)
        if artifact_type == "code":
            review = self._review_code(path, content)
        elif artifact_type == "config":
            review = self._review_config(path, content)
        elif artifact_type == "query":
            review = self._review_query(path, content)
        elif artifact_type == "data_sample":
            review = self._review_data_sample(path, content)
        elif artifact_type == "document":
            review = self._review_document(path, content)
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

    def evaluate_workspace(
        self,
        snapshot: dict | None,
        profile: dict | None = None,
        lessons: list[dict] | None = None,
        interactions: list[dict] | None = None,
    ) -> dict:
        lessons = lessons or []
        interactions = interactions or []
        artifacts = snapshot.get("artifacts", []) if snapshot else []

        if not snapshot and not profile and not lessons:
            return {
                "status": "unconfigured",
                "overall_score": 0.0,
                "tasks": [],
                "summary": "No owner profile, local lessons, or workspace evidence is available for adaptation evaluation.",
                "created_at": time.time(),
            }

        workspace_path = Path(snapshot.get("workspace_path", "")).expanduser() if snapshot else None
        reviews = []
        if workspace_path:
            for artifact in artifacts[:50]:
                path = workspace_path / artifact.get("path", "")
                if not path.exists():
                    continue
                try:
                    reviews.append(self.review_artifact(path, workspace_root=workspace_path))
                except Exception:
                    continue

        evidence = self._build_evidence_index(profile, lessons, interactions, artifacts, reviews)
        tasks = [
            self._build_task(
                "Owner Identity Model",
                evidence["identity"],
                4,
                "Teach Omni your goals, constraints, preferred tone, values, and decision defaults.",
            ),
            self._build_task(
                "Domain Understanding",
                evidence["domain"],
                5,
                "Import more real artifacts and notes that show the vocabulary and facts you rely on.",
            ),
            self._build_task(
                "Workflow Fluency",
                evidence["workflow"],
                4,
                "Add examples of how you perform recurring work, including handoffs, checks, and recovery paths.",
            ),
            self._build_task(
                "Decision Judgment",
                evidence["decision"],
                4,
                "Capture decision criteria, tradeoffs, risk tolerance, and quality standards from your real work.",
            ),
            self._build_task(
                "Feedback Adaptation",
                evidence["feedback"],
                3,
                "Correct the twin during use and store those corrections as explicit feedback lessons.",
            ),
        ]

        overall = round(sum(task["score"] for task in tasks) / max(len(tasks), 1), 2)
        return {
            "status": "ready" if overall >= 80 and all(task["status"] == "ready" for task in tasks) else "training",
            "overall_score": overall,
            "tasks": tasks,
            "summary": f"Personal-twin adaptation scored {overall:.2f} across {len(tasks)} owner-model areas.",
            "created_at": time.time(),
        }

    def _artifact_type(self, path: Path) -> str:
        suffix = path.suffix.lower()
        if suffix in CODE_EXTENSIONS:
            return "code"
        if suffix in CONFIG_EXTENSIONS:
            return "config"
        if suffix in QUERY_EXTENSIONS:
            return "query"
        if suffix in DATA_EXTENSIONS:
            return "data_sample"
        if suffix in DOCUMENT_EXTENSIONS:
            return "document"
        return "artifact"

    def _review_code(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        findings = []
        strengths = []
        function_count = 0
        parsed = False
        if path.suffix.lower() == ".py":
            try:
                tree = ast.parse(content)
                function_count = len([node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)])
                parsed = True
            except SyntaxError:
                findings.append(self._finding("high", "Code does not parse", "The Python artifact has a syntax error.", "Fix parsing before using it as reliable owner evidence.", "Artifact Fluency"))

        metrics = {
            "lines": _line_count(content),
            "function_count": function_count,
            "parsed": parsed,
            "has_tests": _has_any(lowered, ["assert ", "pytest", "unittest", "describe(", "it(", "test_"]),
            "has_error_handling": _has_any(lowered, ["try:", "except ", "catch (", "raise ", "throw "]),
            "has_external_url": bool(re.search(r"https?://", lowered)),
            "has_secret_signal": _has_any(lowered, ["api_key", "secret", "password", "token="]),
            "has_commentary": bool(re.search(r"(^\s*#|//|/\*|\"\"\"|''')", content, flags=re.MULTILINE)),
        }

        if metrics["has_secret_signal"]:
            findings.append(self._finding("critical", "Secret-like token detected", "The artifact appears to contain credential-shaped text.", "Move secrets to local secure configuration and redact this artifact.", "Owner Safety"))
        if metrics["has_external_url"]:
            findings.append(self._finding("high", "External connectivity signal", "The artifact references a network URL.", "Confirm this is disabled or locally mirrored for offline operation.", "Owner Safety"))
        if metrics["lines"] > 25 and not metrics["has_commentary"]:
            findings.append(self._finding("medium", "Intent is underdocumented", "The code is long enough to need local rationale for the twin to learn from it.", "Add comments or a companion note describing purpose, constraints, and owner preference.", "Communication Style"))
        if function_count >= 2 and not metrics["has_tests"]:
            findings.append(self._finding("medium", "Behavior lacks validation evidence", "The code defines behavior without nearby test signals.", "Add tests or an explicit validation checklist.", "Quality Standards"))
        if _has_any(lowered, ["open(", "read_", "write_", "request", "connect", "client"]) and not metrics["has_error_handling"]:
            findings.append(self._finding("medium", "Operational failure path is unclear", "The code appears to touch files or services without visible error handling.", "Add recovery behavior or document expected failure handling.", "Workflow Fluency"))
        if _has_any(lowered, ["todo", "fixme", "hack"]):
            findings.append(self._finding("low", "Unresolved work marker", "The artifact contains TODO/FIXME-style markers.", "Either close the item or preserve it as an explicit training gap.", "Feedback Adaptation"))

        if metrics["has_tests"]:
            strengths.append("Contains validation or test signals.")
        if metrics["has_error_handling"]:
            strengths.append("Contains explicit failure-handling signals.")
        if not findings:
            strengths.append("No obvious owner-adaptation risks detected in code artifact.")

        return {
            "artifact_type": "code",
            "metrics": metrics,
            "findings": findings,
            "strengths": strengths,
            "suggested_tests": ["Add a local smoke test that proves this behavior works offline."] if not metrics["has_tests"] else [],
        }

    def _review_config(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        findings = []
        strengths = []
        parsed = False
        if path.suffix.lower() == ".json":
            try:
                json.loads(content)
                parsed = True
            except json.JSONDecodeError:
                findings.append(self._finding("high", "Config does not parse", "The JSON artifact is invalid.", "Fix the config before using it as trusted local evidence.", "Artifact Fluency"))

        metrics = {
            "lines": _line_count(content),
            "parsed": parsed,
            "has_owner": _has_any(lowered, ["owner", "maintainer", "contact"]),
            "has_purpose": _has_any(lowered, ["purpose", "description", "summary"]),
            "has_external_url": bool(re.search(r"https?://", lowered)),
            "has_secret_signal": _has_any(lowered, ["api_key", "secret", "password", "token"]),
        }
        if metrics["has_secret_signal"]:
            findings.append(self._finding("critical", "Secret-like config value", "Credential-shaped text appears in config.", "Move private values to a local secret store and document only the key names.", "Owner Safety"))
        if metrics["has_external_url"]:
            findings.append(self._finding("high", "External dependency signal", "The config references a network URL.", "Replace with a local endpoint, local mirror, or explicit offline guard.", "Owner Safety"))
        if metrics["lines"] > 8 and not metrics["has_purpose"]:
            findings.append(self._finding("low", "Config purpose is unclear", "The config lacks a visible description or purpose field.", "Add purpose metadata so the twin can learn why this setting matters.", "Domain Understanding"))
        if not metrics["has_owner"]:
            findings.append(self._finding("low", "Ownership metadata missing", "No owner or maintainer signal was detected.", "Add owner/context metadata for future triage.", "Workflow Fluency"))
        if not findings:
            strengths.append("Config is locally readable and carries enough context for adaptation.")
        return {
            "artifact_type": "config",
            "metrics": metrics,
            "findings": findings,
            "strengths": strengths,
            "suggested_tests": ["Add a local config load test."] if path.suffix.lower() == ".json" and not parsed else [],
        }

    def _review_query(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        findings = []
        strengths = []
        metrics = {
            "lines": _line_count(content),
            "has_projection": not bool(re.search(r"select\s+\*", lowered)),
            "has_filter": bool(re.search(r"\bwhere\b", lowered)),
            "has_validation_terms": _has_any(lowered, ["assert", "test", "validate", "expected", "quality"]),
            "has_commentary": bool(re.search(r"--|/\*", content)),
        }
        if not metrics["has_projection"]:
            findings.append(self._finding("medium", "Unbounded projection", "The query selects all fields, which obscures intent and schema expectations.", "Name the fields that matter to the owner's task.", "Artifact Fluency"))
        if metrics["lines"] > 10 and not metrics["has_commentary"]:
            findings.append(self._finding("low", "Query intent is not explained", "The query has multiple lines but no rationale.", "Document the purpose, assumptions, and expected result.", "Domain Understanding"))
        if not metrics["has_validation_terms"]:
            findings.append(self._finding("low", "Expected result is implicit", "No validation or expected-result signal was detected.", "Add a note or test describing what correct output looks like.", "Quality Standards"))
        if not findings:
            strengths.append("Query has clear enough shape for owner-model learning.")
        return {
            "artifact_type": "query",
            "metrics": metrics,
            "findings": findings,
            "strengths": strengths,
            "suggested_tests": ["Capture expected row count, invariant, or acceptance check for this query."] if not metrics["has_validation_terms"] else [],
        }

    def _review_data_sample(self, path: Path, content: str) -> dict:
        delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
        rows = list(csv.reader(content.splitlines()[:20], delimiter=delimiter))
        header = rows[0] if rows else []
        duplicate_headers = [name for name, count in Counter(header).items() if name and count > 1]
        findings = []
        if not header:
            findings.append(self._finding("high", "Data sample has no header", "The sample lacks column names.", "Add a header or companion schema note.", "Domain Understanding"))
        if duplicate_headers:
            findings.append(self._finding("medium", "Duplicate data headers", f"Duplicate header(s): {', '.join(duplicate_headers)}.", "Rename duplicate columns or document the meaning.", "Quality Standards"))
        if len(rows) < 3:
            findings.append(self._finding("low", "Small sample", "The sample has too few rows to teach reliable patterns.", "Add representative examples and edge cases.", "Domain Understanding"))
        return {
            "artifact_type": "data_sample",
            "metrics": {"rows_sampled": len(rows), "columns": len(header), "duplicate_headers": duplicate_headers},
            "findings": findings,
            "strengths": ["Data sample can teach vocabulary and structure."] if header else [],
            "suggested_tests": ["Add a schema description and examples of valid, invalid, and edge-case records."],
        }

    def _review_document(self, path: Path, content: str) -> dict:
        lowered = content.lower()
        headings = len(re.findall(r"^#+\s+|^[A-Z][A-Za-z0-9 ,/-]+:\s*$", content, flags=re.MULTILINE))
        checks = {
            "purpose": _has_any(lowered, ["purpose", "goal", "objective", "why"]),
            "steps": _has_any(lowered, ["step", "process", "workflow", "procedure", "checklist"]),
            "validation": _has_any(lowered, ["validate", "verify", "test", "success", "acceptance"]),
            "decision": _has_any(lowered, ["decision", "tradeoff", "risk", "criteria", "standard"]),
            "feedback": _has_any(lowered, ["feedback", "correction", "preference", "style", "tone"]),
        }
        findings = []
        if _line_count(content) > 12 and headings == 0:
            findings.append(self._finding("low", "Document needs structure", "The document is long but has no headings.", "Add sections so the twin can separate context, action, and standard.", "Communication Style"))
        for key, present in checks.items():
            if present:
                continue
            severity = "medium" if key in {"purpose", "validation"} else "low"
            findings.append(self._finding(severity, f"Document missing {key}", f"No {key} signal was detected.", f"Add {key} details that show how the owner thinks and works.", self._competency_for_check(key)))
        strengths = [f"Document includes {key} signal." for key, present in checks.items() if present]
        return {
            "artifact_type": "document",
            "metrics": {"lines": _line_count(content), "headings": headings, **checks},
            "findings": findings,
            "strengths": strengths or ["Document text is available for owner-model learning."],
            "suggested_tests": ["Ask Omni to summarize this artifact, then correct the summary to teach personal style."],
        }

    def _review_generic(self, path: Path, content: str) -> dict:
        return {
            "artifact_type": "artifact",
            "metrics": {"lines": _line_count(content), "suffix": path.suffix.lower()},
            "findings": [self._finding("low", "Generic artifact", "This file type has no specialized local parser yet.", "Add a companion note describing its purpose, owner use, and quality standard.", "Domain Understanding")],
            "strengths": ["Artifact is available for local memory."],
            "suggested_tests": [],
        }

    def _build_evidence_index(
        self,
        profile: dict | None,
        lessons: list[dict],
        interactions: list[dict],
        artifacts: list[dict],
        reviews: list[dict],
    ) -> dict[str, list[str]]:
        evidence = {key: [] for key in ["identity", "domain", "workflow", "decision", "feedback"]}
        if profile:
            for goal in profile.get("goals", []):
                evidence["identity"].append(f"Goal: {goal}")
            for constraint in profile.get("constraints", []):
                evidence["identity"].append(f"Constraint: {constraint}")
            if profile.get("role_description"):
                evidence["domain"].append(f"Role context: {profile['role_description']}")
            for value in profile.get("values", []):
                evidence["identity"].append(f"Value: {value}")
            for principle in profile.get("decision_principles", []):
                evidence["decision"].append(f"Decision principle: {principle}")

        for artifact in artifacts:
            text = " ".join([
                artifact.get("path", ""),
                artifact.get("summary", ""),
                " ".join(artifact.get("skill_tags", [])),
                " ".join(artifact.get("signals", [])),
            ]).lower()
            evidence["domain"].append(f"Artifact: {artifact.get('path')}")
            if _has_any(text, ["workflow", "process", "step", "procedure", "runbook", "handoff", "schedule"]):
                evidence["workflow"].append(f"Workflow artifact: {artifact.get('path')}")
            if _has_any(text, ["risk", "decision", "tradeoff", "quality", "validation", "criteria", "standard"]):
                evidence["decision"].append(f"Decision artifact: {artifact.get('path')}")

        for review in reviews:
            if review.get("score", 0) >= 75:
                evidence["domain"].append(f"Reviewed artifact: {review.get('path')}")
            for finding in review.get("findings", []):
                competency = finding.get("competency", "").lower()
                if "workflow" in competency:
                    evidence["workflow"].append(finding["title"])
                if "quality" in competency or "decision" in competency:
                    evidence["decision"].append(finding["title"])

        for lesson in lessons:
            text = " ".join([
                lesson.get("title", ""),
                lesson.get("content", ""),
                lesson.get("lesson_type", ""),
                " ".join(lesson.get("skill_tags", [])),
            ]).lower()
            title = lesson.get("title", "Lesson")
            if _has_any(text, ["identity", "preference", "style", "tone", "value", "goal", "constraint"]):
                evidence["identity"].append(title)
            if _has_any(text, ["domain", "term", "rule", "concept", "artifact", "knowledge"]):
                evidence["domain"].append(title)
            if _has_any(text, ["workflow", "process", "step", "procedure", "runbook", "handoff"]):
                evidence["workflow"].append(title)
            if _has_any(text, ["decision", "tradeoff", "risk", "standard", "criteria", "quality"]):
                evidence["decision"].append(title)
            if _has_any(text, ["feedback", "correction", "wrong", "prefer", "instead", "self_reflection"]):
                evidence["feedback"].append(title)

        for interaction in interactions:
            text = " ".join([interaction.get("query", ""), interaction.get("response", ""), interaction.get("action_result", "") or ""]).lower()
            if text:
                evidence["feedback"].append(f"Interaction: {interaction.get('id', 'recent')}")
            if _has_any(text, ["prefer", "correction", "instead", "not like that", "my style"]):
                evidence["identity"].append(f"Preference interaction: {interaction.get('id', 'recent')}")
                evidence["feedback"].append(f"Correction interaction: {interaction.get('id', 'recent')}")
        return {key: list(dict.fromkeys(value)) for key, value in evidence.items()}

    def _build_task(self, name: str, evidence: list[str], target: int, next_step: str) -> dict:
        score = round(min(100.0, (len(evidence) / max(target, 1)) * 100.0), 2)
        return {
            "name": name,
            "status": "ready" if score >= 75 else "needs_work",
            "score": score,
            "evidence": evidence[:5],
            "next_step": "Use this owner-model area on live work and correct it when it misses." if score >= 75 else next_step,
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
        label = artifact_type.replace("_", " ").title()
        if findings:
            counts = Counter(finding["severity"] for finding in findings)
            finding_text = ", ".join(f"{count} {severity}" for severity, count in counts.items())
            return f"{label} scored {score:.0f} with {finding_text} owner-model finding(s)."
        return f"{label} scored {score:.0f}. {strengths[0] if strengths else 'No obvious issues detected.'}"

    def _competency_for_check(self, key: str) -> str:
        return {
            "purpose": "Domain Understanding",
            "steps": "Workflow Fluency",
            "validation": "Quality Standards",
            "decision": "Decision Judgment",
            "feedback": "Feedback Adaptation",
        }.get(key, "Owner Model")
