"""Canonical data contracts for one inspection.

Why this module exists (maintainability review, Phase B.1): the pipeline grew
several near-duplicate shapes for the same concept (a fusion dict, a batch
summary dict, an API response dict, a report payload). Five representations of
one onion prediction is how a demo drifts away from the product. Here the
contracts live **once**, with:

* dataclasses that say exactly which fields exist and which are `None`;
* ``from_dict`` constructors that tolerate missing optional fields but never
  invent a value for a missing *measurement* (`None` means not measured);
* validation used by the API layer and by conformance tests that run the real
  pipeline and assert its output still matches these contracts.

The contracts intentionally describe the *shape we promise*. They are verified
against real pipeline output in ``tests/contracts/test_contract_conformance.py``
rather than trusted by assumption.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

SCHEMA_VERSION = "1.0.0"

#: Acoustic dataset classes. Only the first may ever influence a grade.
VERIFIED_ONION_ACOUSTIC = "verified_onion_acoustic"
ACOUSTIC_DATASET_TYPES = (
    VERIFIED_ONION_ACOUSTIC,
    "related_produce_acoustic",
    "generic_audio_pretraining",
    "paper_only",
    "synthetic",
    "unknown",
)

DECISIONS = ("grade_a", "relaxed", "reject", "manual_review", "not_onion")
SIZE_METHODS = ("aruco_calibrated", "uncalibrated", "unknown", "unavailable")


class ContractError(ValueError):
    """Raised when a payload does not satisfy its contract."""


def _require(payload: Dict[str, Any], keys: tuple, where: str) -> None:
    missing = [k for k in keys if k not in payload]
    if missing:
        raise ContractError(f"{where} is missing required field(s): {missing}")


def _get_bool(payload: Dict[str, Any], key: str) -> Optional[bool]:
    value = payload.get(key)
    return None if value is None else bool(value)


def _get_float(payload: Dict[str, Any], key: str) -> Optional[float]:
    value = payload.get(key)
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise ContractError(f"{key} must be numeric or null, got {value!r}") from exc


@dataclass
class SizeResult:
    """Physical size of one onion. ``diameter_mm`` is None when uncalibrated."""

    diameter_mm: Optional[float] = None
    size_method: str = "unknown"
    calibration_confidence: Optional[float] = None
    markers_detected: int = 0
    pixel_diameter: Optional[float] = None
    warnings: List[str] = field(default_factory=list)
    notes: str = ""

    def __post_init__(self) -> None:
        if self.size_method not in SIZE_METHODS:
            raise ContractError(f"unknown size_method: {self.size_method!r}")
        if self.size_method == "aruco_calibrated" and self.diameter_mm is None:
            raise ContractError("aruco_calibrated requires a diameter_mm value")
        if self.size_method != "aruco_calibrated" and self.diameter_mm is not None:
            # A millimetre figure without calibration would be a fabricated
            # physical measurement — the exact claim this project refuses to make.
            raise ContractError(
                "diameter_mm may only be reported when size_method is "
                "'aruco_calibrated'")

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "SizeResult":
        return cls(
            diameter_mm=_get_float(payload, "diameter_mm"),
            size_method=str(payload.get("size_method", "unknown")),
            calibration_confidence=_get_float(payload, "calibration_confidence"),
            markers_detected=int(payload.get("markers_detected") or 0),
            pixel_diameter=_get_float(payload, "pixel_diameter"),
            warnings=list(payload.get("warnings") or []),
            notes=str(payload.get("notes") or ""),
        )


@dataclass
class VisionResult:
    """Visible-condition result for one onion.

    This describes the ``vision`` block of the shared interface (label,
    confidence, defects, model version). The object-level question (is this an
    onion at all?) lives at the top level of the vision response, so
    ``is_onion`` is optional here: ``None`` means the block alone does not
    answer it, which is different from ``False``.
    """

    label: str
    confidence: Optional[float]
    is_onion: Optional[bool] = None
    defects: Dict[str, Any] = field(default_factory=dict)
    model_version: str = ""
    status: str = "success"
    warnings: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "VisionResult":
        _require(payload, ("label",), "VisionResult")
        return cls(
            label=str(payload["label"]),
            is_onion=(None if payload.get("is_onion") is None
                      else bool(payload["is_onion"])),
            confidence=_get_float(payload, "confidence"),
            defects=dict(payload.get("defects") or {}),
            model_version=str(payload.get("model_version") or ""),
            status=str(payload.get("status", "success")),
            warnings=list(payload.get("warnings") or []),
        )

    @property
    def quality_class(self) -> Optional[str]:
        """Never sourced from the vision block.

        The commercial 4-class head is research-only; keeping it out of this
        contract means production code cannot read it through the canonical
        shape even by accident.
        """
        return None


@dataclass
class DefectReading:
    """One binary defect with its probability. Never a bare 0.0 for unknown."""

    probability: Optional[float]
    detected: Optional[bool]

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "DefectReading":
        return cls(probability=_get_float(payload, "probability"),
                   detected=payload.get("detected"))


@dataclass
class AcousticResult:
    """Acoustic evidence. ``research_only`` blocks it from grading forever."""

    status: str
    internal_defect_probability: Optional[float] = None
    confidence: Optional[float] = None
    audio_quality: Dict[str, Any] = field(default_factory=dict)
    features: Optional[Dict[str, Any]] = None
    model_version: str = ""
    dataset_types: List[str] = field(default_factory=list)
    ground_truth_verified: bool = False
    research_only: bool = True
    warnings: List[str] = field(default_factory=list)

    @property
    def grading_eligible(self) -> bool:
        """The one place that decides whether acoustics may move a grade."""
        return acoustic_grading_eligible(self)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "AcousticResult":
        _require(payload, ("status",), "AcousticResult")
        dataset_types = payload.get("dataset_type") or payload.get("dataset_types") or []
        if isinstance(dataset_types, str):
            dataset_types = [dataset_types]
        return cls(
            status=str(payload["status"]),
            internal_defect_probability=_get_float(
                payload, "internal_defect_probability"),
            confidence=_get_float(payload, "confidence"),
            audio_quality=dict(payload.get("audio_quality") or {}),
            features=payload.get("features"),
            model_version=str(payload.get("model_version") or ""),
            dataset_types=[str(t) for t in dataset_types],
            ground_truth_verified=bool(payload.get("ground_truth_verified", False)),
            research_only=bool(payload.get("research_only", True)),
            warnings=list(payload.get("warnings") or []),
        )


def acoustic_grading_eligible(acoustic: Optional[Any]) -> bool:
    """May this acoustic evidence influence a procurement decision?

    Yes only when **all** hold:

    * the recording passed the quality gates (``status == "valid"``);
    * the model was trained on verified onion ground truth
      (``dataset_type`` includes ``verified_onion_acoustic``);
    * the caller did not mark it research-only / unverified.

    The implementation is deliberately strict and centralised: fusion, Deep
    Scan and any future caller share it, so "synthetic audio changed a grade"
    cannot happen through a forgotten key.
    """
    if not acoustic:
        return False
    if isinstance(acoustic, AcousticResult):
        dataset_types = acoustic.dataset_types
        if acoustic.status != "valid":
            return False
        if acoustic.research_only or not acoustic.ground_truth_verified:
            return False
    else:
        if str(acoustic.get("status")) != "valid":
            return False
        if acoustic.get("research_only") is True:
            return False
        if acoustic.get("ground_truth_verified") is False:
            return False
        raw = acoustic.get("dataset_type") or acoustic.get("dataset_types") or []
        dataset_types = [raw] if isinstance(raw, str) else list(raw)
        # Absent metadata is treated as "not verified": silence is not evidence.
        if not dataset_types:
            return False
    return VERIFIED_ONION_ACOUSTIC in dataset_types


@dataclass
class OnionMeasurement:
    """Everything measured about one onion. ``None`` means not measured."""

    onion_id: str
    diameter_mm: Optional[float] = None
    size_method: str = "unknown"
    rot_detected: Optional[bool] = None
    rot_confidence: Optional[float] = None
    sprout_detected: Optional[bool] = None
    sprout_confidence: Optional[float] = None
    damage_surface_pct: Optional[float] = None
    internal_defect_probability: Optional[float] = None
    internal_evidence_valid: bool = False
    model_confidence: Optional[float] = None
    occlusion_fraction: Optional[float] = None

    #: Field order used both by the grading engine and by report rendering.
    FIELDS = ("diameter_mm", "size_method", "rot_detected", "rot_confidence",
              "sprout_detected", "sprout_confidence", "damage_surface_pct",
              "internal_defect_probability", "internal_evidence_valid",
              "model_confidence", "occlusion_fraction")

    @classmethod
    def from_dict(cls, payload: Dict[str, Any], onion_id: str = "") -> "OnionMeasurement":
        return cls(
            onion_id=onion_id or str(payload.get("onion_id") or ""),
            diameter_mm=_get_float(payload, "diameter_mm"),
            size_method=str(payload.get("size_method", "unknown")),
            rot_detected=_get_bool(payload, "rot_detected"),
            rot_confidence=_get_float(payload, "rot_confidence"),
            sprout_detected=_get_bool(payload, "sprout_detected"),
            sprout_confidence=_get_float(payload, "sprout_confidence"),
            damage_surface_pct=_get_float(payload, "damage_surface_pct"),
            internal_defect_probability=_get_float(
                payload, "internal_defect_probability"),
            internal_evidence_valid=bool(payload.get("internal_evidence_valid")),
            model_confidence=_get_float(payload, "model_confidence"),
            occlusion_fraction=_get_float(payload, "occlusion_fraction"),
        )


@dataclass
class GradingDecision:
    decision: str
    reason_codes: List[str]
    policy_id: str
    policy_version: str
    policy_hash: str
    policy_verified: bool
    measurements: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.decision not in DECISIONS:
            raise ContractError(f"unknown decision: {self.decision!r}")
        if not self.reason_codes:
            raise ContractError("a decision must carry at least one reason code")

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "GradingDecision":
        _require(payload, ("decision", "reason_codes"), "GradingDecision")
        return cls(
            decision=str(payload["decision"]),
            reason_codes=list(payload["reason_codes"]),
            policy_id=str(payload.get("policy_id") or ""),
            policy_version=str(payload.get("policy_version") or ""),
            policy_hash=str(payload.get("policy_hash") or ""),
            policy_verified=bool(payload.get("policy_verified")),
            measurements=dict(payload.get("measurements") or {}),
        )


@dataclass
class BatchResult:
    batch_id: str
    center_id: str
    inspector_id: str
    totals: Dict[str, int]
    counts: Dict[str, int]
    percentages: Dict[str, float]
    policy: Dict[str, Any] = field(default_factory=dict)
    model_versions: Dict[str, str] = field(default_factory=dict)
    created_at: str = ""
    lot_id: Optional[str] = None
    denominator_note: str = ""
    notes: str = ""

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "BatchResult":
        _require(payload, ("batch_id", "center_id", "totals", "counts"), "BatchResult")
        return cls(
            batch_id=str(payload["batch_id"]),
            center_id=str(payload["center_id"]),
            inspector_id=str(payload.get("inspector_id") or ""),
            totals=dict(payload["totals"]),
            counts=dict(payload["counts"]),
            percentages=dict(payload.get("percentages") or {}),
            policy=dict(payload.get("policy") or {}),
            model_versions=dict(payload.get("model_versions") or {}),
            created_at=str(payload.get("created_at") or ""),
            lot_id=payload.get("lot_id"),
            denominator_note=str(payload.get("denominator_note") or ""),
            notes=str(payload.get("notes") or ""),
        )

    def check_percentages(self, tolerance: float = 0.05) -> List[str]:
        """Percentages must reconcile with counts (audit-friendliness)."""
        problems: List[str] = []
        total = int(self.totals.get("total_detected", 0)) or 0
        for name, count in self.counts.items():
            expected = 100.0 * count / total if total else 0.0
            actual = float(self.percentages.get(name, 0.0))
            if abs(expected - actual) > tolerance:
                problems.append(
                    f"{name}: reported {actual}% but {count}/{total} = "
                    f"{round(expected, 2)}%")
        return problems


@dataclass
class HumanOverride:
    """An inspector's decision, stored beside (never instead of) the machine's."""

    onion_id: str
    human_decision: str
    inspector_id: str = ""
    batch_id: Optional[str] = None
    machine_decision: Optional[str] = None
    machine_confidence: Optional[float] = None
    reason_code: str = ""
    note: str = ""
    override_id: Optional[str] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        if self.human_decision not in DECISIONS:
            raise ContractError(f"unknown human_decision: {self.human_decision!r}")

    @property
    def is_disagreement(self) -> bool:
        return (self.machine_decision is not None
                and self.machine_decision != self.human_decision)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "HumanOverride":
        _require(payload, ("onion_id", "human_decision"), "HumanOverride")
        return cls(
            onion_id=str(payload["onion_id"]),
            human_decision=str(payload["human_decision"]),
            inspector_id=str(payload.get("inspector_id") or ""),
            batch_id=payload.get("batch_id"),
            machine_decision=payload.get("machine_decision"),
            machine_confidence=_get_float(payload, "machine_confidence"),
            reason_code=str(payload.get("reason_code") or payload.get("reason") or ""),
            note=str(payload.get("note") or ""),
            override_id=payload.get("override_id"),
            created_at=str(payload.get("created_at") or ""),
        )


@dataclass
class InspectionReport:
    report_id: str
    header: Dict[str, Any]
    summary: Dict[str, Any]
    report_version: str = "1.0.0"
    demo_mode: bool = True
    generated_at: str = ""
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    onion_results: List[Dict[str, Any]] = field(default_factory=list)
    integrity: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "InspectionReport":
        _require(payload, ("report_id", "header", "summary"), "InspectionReport")
        header = dict(payload["header"])
        _require(header, ("center_id", "batch_id", "policy_id", "policy_hash"),
                 "InspectionReport.header")
        return cls(
            report_id=str(payload["report_id"]),
            header=header,
            summary=dict(payload["summary"]),
            report_version=str(payload.get("report_version", "1.0.0")),
            demo_mode=bool(payload.get("demo_mode", True)),
            generated_at=str(payload.get("generated_at") or ""),
            evidence=list(payload.get("evidence") or []),
            onion_results=list(payload.get("onion_results") or []),
            integrity=dict(payload.get("integrity") or {}),
        )


#: name → contract, used by the API layer and the conformance tests.
CONTRACTS = {
    "vision": VisionResult,
    "acoustic": AcousticResult,
    "size": SizeResult,
    "measurement": OnionMeasurement,
    "decision": GradingDecision,
    "batch": BatchResult,
    "override": HumanOverride,
    "report": InspectionReport,
}


def contract_names() -> List[str]:
    return sorted(CONTRACTS)


def as_dict(obj: Any) -> Dict[str, Any]:
    """Dataclass → plain dict (for JSON serialisation)."""
    return asdict(obj)
