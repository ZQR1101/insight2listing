"""Amazon US listing platform rules (plan section 12.4).

Deterministic checks over generated / edited listing copy. ``passed`` means no
*errors*; warnings are reported but do not block approval. All limits follow
the first-version rules in the product plan and can be tightened per category
later (section 11.4).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

MAX_TITLE_CHARS = 200
RECOMMENDED_TITLE_CHARS = 80
MAX_BULLETS = 5
MAX_BULLET_CHARS = 500
MIN_BULLET_CHARS = 15
MAX_DESCRIPTION_CHARS = 2000
MAX_SEARCH_TERM_BYTES = 249

#: Absolute, misleading or promotional phrasing (section 12.4).
FORBIDDEN_PHRASES: tuple[str, ...] = (
    "best",
    "#1",
    "top rated",
    "cheapest",
    "guaranteed",
    "risk-free",
    "100% safe",
    "cure",
    "fda approved",
    "eco-friendly",
    "free shipping",
    "on sale",
    "best price",
    "world's leading",
)

_ALLOWED_ACRONYMS = frozenset(
    {"LED", "BPA", "FDA", "USDA", "PP", "PET", "PC", "XL", "CM", "MM", "IN", "OZ", "LBS", "ML"}
)

_CAPS_RUN = re.compile(r"\b[A-Z]{4,}\b")
_WORD = re.compile(r"[a-z]+")


@dataclass(slots=True)
class RuleIssue:
    field: str
    issue: str
    severity: str = "error"  # "error" | "warning"

    def as_dict(self) -> dict[str, str]:
        return {"field": self.field, "issue": self.issue, "severity": self.severity}


@dataclass(slots=True)
class CheckReport:
    passed: bool
    issues: list[RuleIssue] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "issues": [i.as_dict() for i in self.issues],
        }


def _combined_text(
    *, title: str, bullets: list[str], description: str, search_terms: str
) -> str:
    return " \n ".join([title, *bullets, description, search_terms])


def check_listing(
    *,
    title: str,
    bullets: list[str],
    description: str,
    search_terms: str,
) -> CheckReport:
    issues: list[RuleIssue] = []

    # --- title ---
    if not title.strip():
        issues.append(RuleIssue("title", "title is empty"))
    else:
        if len(title) > MAX_TITLE_CHARS:
            issues.append(
                RuleIssue("title", f"title exceeds {MAX_TITLE_CHARS} characters ({len(title)})")
            )
        if len(title) > RECOMMENDED_TITLE_CHARS:
            issues.append(
                RuleIssue(
                    "title",
                    f"title exceeds the recommended {RECOMMENDED_TITLE_CHARS} characters",
                    severity="warning",
                )
            )
        for run in _CAPS_RUN.findall(title):
            if run not in _ALLOWED_ACRONYMS:
                issues.append(
                    RuleIssue("title", f"avoid all-caps word '{run}'", severity="warning")
                )

    # --- bullets ---
    if len(bullets) > MAX_BULLETS:
        issues.append(RuleIssue("bullet_points", f"more than {MAX_BULLETS} bullet points"))
    if not bullets:
        issues.append(RuleIssue("bullet_points", "no bullet points"))
    elif len(bullets) < 3:
        issues.append(
            RuleIssue("bullet_points", "fewer than 3 bullet points", severity="warning")
        )
    for idx, bullet in enumerate(bullets, start=1):
        if len(bullet) > MAX_BULLET_CHARS:
            issues.append(
                RuleIssue(
                    "bullet_points",
                    f"bullet {idx} exceeds {MAX_BULLET_CHARS} characters ({len(bullet)})",
                )
            )
        if len(bullet) < MIN_BULLET_CHARS:
            issues.append(
                RuleIssue("bullet_points", f"bullet {idx} is very short", severity="warning")
            )

    # --- description ---
    if not description.strip():
        issues.append(RuleIssue("description", "description is empty", severity="warning"))
    elif len(description) > MAX_DESCRIPTION_CHARS:
        issues.append(
            RuleIssue(
                "description",
                f"description exceeds {MAX_DESCRIPTION_CHARS} characters",
                severity="warning",
            )
        )
    for run in _CAPS_RUN.findall(description):
        if run not in _ALLOWED_ACRONYMS:
            issues.append(
                RuleIssue("description", f"avoid all-caps word '{run}'", severity="warning")
            )

    # --- search terms ---
    if len(search_terms.encode("utf-8")) > MAX_SEARCH_TERM_BYTES:
        issues.append(
            RuleIssue(
                "search_terms",
                f"search terms exceed {MAX_SEARCH_TERM_BYTES} bytes",
            )
        )

    # --- forbidden / promotional phrasing ---
    combined = _combined_text(
        title=title, bullets=bullets, description=description, search_terms=search_terms
    ).lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in combined:
            issues.append(
                RuleIssue("content", f"absolute or promotional claim: '{phrase}'")
            )

    # --- keyword stuffing ---
    words = _WORD.findall(combined)
    counts: dict[str, int] = {}
    for word in words:
        counts[word] = counts.get(word, 0) + 1
    for word, count in sorted(counts.items()):
        if count > 5:
            issues.append(
                RuleIssue(
                    "content",
                    f"possible keyword stuffing: '{word}' used {count} times",
                    severity="warning",
                )
            )

    return CheckReport(passed=not any(i.severity == "error" for i in issues), issues=issues)


def check_fact_usage(
    *,
    bullets: list[dict[str, Any]],
    confirmed_fact_ids: set[str],
) -> CheckReport:
    """Every bullet reference must point at a confirmed, non-expired fact."""
    issues: list[RuleIssue] = []
    for idx, bullet in enumerate(bullets, start=1):
        for fact_id in bullet.get("fact_ids", []) or []:
            if str(fact_id) not in confirmed_fact_ids:
                issues.append(
                    RuleIssue(
                        "bullet_points",
                        f"bullet {idx} references a fact that is not confirmed",
                    )
                )
        for insight_id in bullet.get("insight_ids", []) or []:
            if not str(insight_id):
                issues.append(RuleIssue("bullet_points", f"bullet {idx} has an empty insight ref"))
    return CheckReport(passed=not any(i.severity == "error" for i in issues), issues=issues)
