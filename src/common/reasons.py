"""Machine-readable reason codes.

Used by the grading engine, fusion, reports and analytics so that a decision
can always be explained, translated and aggregated without parsing prose.
"""
from __future__ import annotations

from typing import Dict, List

VISIBLE_ROT = "VISIBLE_ROT"
SPROUT_DETECTED = "SPROUT_DETECTED"
BELOW_SIZE_THRESHOLD = "BELOW_SIZE_THRESHOLD"
ABOVE_SIZE_THRESHOLD = "ABOVE_SIZE_THRESHOLD"
BELOW_GRADE_A_SIZE = "BELOW_GRADE_A_SIZE"
SURFACE_DAMAGE_EXCEEDS = "SURFACE_DAMAGE_EXCEEDS"
INTERNAL_DEFECT_RISK = "INTERNAL_DEFECT_RISK"
LOW_MODEL_CONFIDENCE = "LOW_MODEL_CONFIDENCE"
AUDIO_UNRELIABLE = "AUDIO_UNRELIABLE"
MULTIMODAL_DISAGREEMENT = "MULTIMODAL_DISAGREEMENT"
CALIBRATION_MISSING = "CALIBRATION_MISSING"
OCCLUSION_HIGH = "OCCLUSION_HIGH"
MEASUREMENT_UNAVAILABLE = "MEASUREMENT_UNAVAILABLE"
NOT_AN_ONION = "NOT_AN_ONION"
MODEL_UNAVAILABLE = "MODEL_UNAVAILABLE"
POLICY_UNVERIFIED = "POLICY_UNVERIFIED"
ACOUSTIC_NOT_VALIDATED = "ACOUSTIC_NOT_VALIDATED"

#: Human-readable, non-technical wording for each code (farmer/report views).
DESCRIPTIONS: Dict[str, str] = {
    VISIBLE_ROT: "Visible rot detected on the bulb surface.",
    SPROUT_DETECTED: "Sprouting detected.",
    BELOW_SIZE_THRESHOLD: "Size below the selected policy's minimum diameter.",
    ABOVE_SIZE_THRESHOLD: "Size above the selected policy's maximum diameter.",
    BELOW_GRADE_A_SIZE: "Size is outside the Grade-A range but within the relaxed range.",
    SURFACE_DAMAGE_EXCEEDS: "Surface damage exceeds the allowed percentage.",
    INTERNAL_DEFECT_RISK: "Acoustic evidence indicates possible internal defect.",
    LOW_MODEL_CONFIDENCE: "Model confidence is below the policy threshold.",
    AUDIO_UNRELIABLE: "Acoustic recording was not reliable; visual result kept.",
    MULTIMODAL_DISAGREEMENT: "Visual and acoustic evidence disagree.",
    CALIBRATION_MISSING: "Size reference (calibration mat) was not detected.",
    OCCLUSION_HIGH: "Onions are too crowded/overlapping to grade reliably.",
    MEASUREMENT_UNAVAILABLE: "A measurement required by the policy is unavailable.",
    NOT_AN_ONION: "The object is not an onion.",
    MODEL_UNAVAILABLE: "A required model artifact is not available.",
    POLICY_UNVERIFIED: "The active grading policy is a demo policy, not an official standard.",
    ACOUSTIC_NOT_VALIDATED: "Acoustic model has no verified onion ground truth.",
}


def describe(code: str) -> str:
    return DESCRIPTIONS.get(code, code)


def describe_all(codes: List[str]) -> List[str]:
    return [describe(c) for c in codes]
