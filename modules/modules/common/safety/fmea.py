"""
fmea.py — FMEA (Failure Mode and Effects Analysis) with S1/S2/S3 classification.

Per M8 (Segurança e Ética) from INSTRUCTIONS:
  S1 = safety critical — failure = risk of life
  S2 = safety relevant — failure = significant material damage
  S3 = standard safety — failure = inconvenience without physical damage

FMEA scoring: RPN = Severity × Occurrence × Detection (each 1-10)
RPN > 200 requires redesign before proceeding.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any


class SafetyLevel(IntEnum):
    S3_STANDARD = 3   # Inconvenience only
    S2_RELEVANT = 2   # Material damage
    S1_CRITICAL = 1   # Risk of life


class Severity(IntEnum):
    NONE = 1
    MINOR = 2
    MODERATE = 3
    SIGNIFICANT = 4
    MAJOR = 5
    SEVERE = 6
    CRITICAL = 7
    EXTREME = 8
    SERIOUS_INJURY = 9
    FATAL = 10


class Occurrence(IntEnum):
    REMOTE = 1       # < 1/10k
    LOW = 2          # 1/5k
    MODERATE = 3     # 1/2k
    FREQUENT = 4     # 1/500
    HIGH = 5         # 1/200
    REPEATED = 6     # 1/100
    LIKELY = 7       # 1/50
    VERY_LIKELY = 8  # 1/20
    PROBABLE = 9     # 1/10
    CERTAIN = 10     # > 1/3


class Detection(IntEnum):
    ALWAYS_CAUGHT = 1
    HIGH_LIKELIHOOD = 2
    MODERATE = 3
    LIKELY = 4
    LOW = 5
    UNLIKELY = 6
    HARD_TO_DETECT = 7
    VERY_HARD = 8
    EXTREMELY_HARD = 9
    IMPOSSIBLE = 10


@dataclass
class FailureMode:
    """A single failure mode entry in FMEA."""

    component: str
    failure_mode: str
    cause: str
    effect: str
    severity: Severity
    occurrence: Occurrence
    detection: Detection
    mitigation: str = ""

    @property
    def rpn(self) -> int:
        return self.severity * self.occurrence * self.detection

    @property
    def safety_level(self) -> SafetyLevel:
        if self.severity >= Severity.CRITICAL:
            return SafetyLevel.S1_CRITICAL
        elif self.severity >= Severity.MODERATE:
            return SafetyLevel.S2_RELEVANT
        return SafetyLevel.S3_STANDARD

    @property
    def requires_redesign(self) -> bool:
        return self.rpn > 200

    def to_dict(self) -> dict[str, Any]:
        return {
            "component": self.component,
            "failure_mode": self.failure_mode,
            "cause": self.cause,
            "effect": self.effect,
            "severity": self.severity.value,
            "occurrence": self.occurrence.value,
            "detection": self.detection.value,
            "rpn": self.rpn,
            "safety_level": self.safety_level.name,
            "requires_redesign": self.requires_redesign,
            "mitigation": self.mitigation,
        }


@dataclass
class FMEAResult:
    """Complete FMEA for a system."""

    system_name: str
    failures: list[FailureMode] = field(default_factory=list)

    def add(self, failure: FailureMode):
        self.failures.append(failure)

    @property
    def top_rpn(self) -> list[FailureMode]:
        return sorted(self.failures, key=lambda f: f.rpn, reverse=True)[:5]

    @property
    def safety_critical(self) -> list[FailureMode]:
        return [f for f in self.failures if f.safety_level == SafetyLevel.S1_CRITICAL]

    @property
    def redesign_required(self) -> list[FailureMode]:
        return [f for f in self.failures if f.requires_redesign]

    def summary(self) -> dict[str, Any]:
        return {
            "system": self.system_name,
            "total_failures": len(self.failures),
            "safety_critical": len(self.safety_critical),
            "redesign_required": len(self.redesign_required),
            "top_5_rpn": [f.to_dict() for f in self.top_rpn],
        }


def classify_safety_level(sigma_applied_MPa: float,
                           sigma_yield_MPa: float) -> SafetyLevel:
    """Classify safety level based on stress ratio."""
    ratio = sigma_applied_MPa / sigma_yield_MPa if sigma_yield_MPa > 0 else 99
    if ratio > 0.9:
        return SafetyLevel.S1_CRITICAL
    elif ratio > 0.6:
        return SafetyLevel.S2_RELEVANT
    return SafetyLevel.S3_STANDARD
