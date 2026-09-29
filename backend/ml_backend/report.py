"""
Digital Audit & Traceability Report Generation Engine
Generates tamper-verifiable digital inspection reports (HTML + certified PDF + QR Code)
with cryptographic SHA-256 audit hashing for farmer-mandi dispute resolution.
"""
from __future__ import annotations
import hashlib
import json
import uuid
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any
from datetime import datetime

import qrcode
from PIL import Image
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image as RLImage,
    KeepTogether,
)

from ml_backend.vision.grade import grade_batch, OnionResult


def compute_audit_hash(
    report_id: str,
    batch_id: str,
    farmer_id: str,
    officer_id: str,
    centre: str,
    batch_stats: Dict[str, Any],
    results: List[OnionResult],
) -> str:
    """Computes a deterministic SHA-256 cryptographic audit hash over the inspection ledger."""
    canonical_payload = {
        "report_id": report_id,
        "batch_id": batch_id,
        "farmer_id": farmer_id,
        "officer_id": officer_id,
        "centre": centre,
        "summary": batch_stats,
        "items": [
            {
                "id": r.onion_id,
                "diameter_mm": r.diameter_mm,
                "grade": r.final_grade,
                "confidence": r.confidence,
                "reasons": r.reason_codes,
            }
            for r in results
        ],
    }
    encoded = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def generate_qr_code(data: str) -> Image.Image:
    """Generates high-contrast QR code image."""
    qr = qrcode.QRCode(version=1, box_size=10, border=3)
    qr.add_data(data)
    qr.make(fit=True)
    pil_img = qr.make_image(fill_color="black", back_color="white")
    return Image.fromarray(np.array(pil_img.get_image()))


def generate_report(
    batch_id: str,
    farmer_id: str,
    officer_id: str,
    centre: str,
    policy: dict,
    results: list[OnionResult],
    original_image: np.ndarray,
    annotated_image: np.ndarray,
    gps: Optional[Tuple[float, float]] = None,
    output_dir: str = "reports",
) -> str:
    """
    Generate verifiable HTML + certified PDF report with QR code and cryptographic audit seal.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # Collision-resistant report ID with cryptographic suffix
    unique_suffix = uuid.uuid4().hex[:6].upper()
    report_id = f"ONION-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{unique_suffix}"

    batch_stats = grade_batch(results)
    audit_hash = compute_audit_hash(
        report_id=report_id,
        batch_id=batch_id,
        farmer_id=farmer_id,
        officer_id=officer_id,
        centre=centre,
        batch_stats=batch_stats,
        results=results,
    )

    # Convert numpy images to PIL
    orig_pil = Image.fromarray(original_image) if isinstance(original_image, np.ndarray) else original_image
    annot_pil = Image.fromarray(annotated_image) if isinstance(annotated_image, np.ndarray) else annotated_image

    # QR code points to local verification endpoint with audit hash
    verify_url = f"http://127.0.0.1:5000/reports/{report_id}/verify?hash={audit_hash[:16]}"
    qr_img = generate_qr_code(verify_url)

    # Save artifact files
    annot_path = out_path / f"{report_id}_annotated.png"
    orig_path = out_path / f"{report_id}_original.png"
    qr_path = out_path / f"{report_id}_qr.png"
    meta_path = out_path / f"{report_id}_metadata.json"

    annot_pil.save(annot_path, format="PNG")
    orig_pil.save(orig_path, format="PNG")
    qr_img.save(qr_path, format="PNG")

    metadata = {
        "report_id": report_id,
        "batch_id": batch_id,
        "farmer_id": farmer_id,
        "officer_id": officer_id,
        "centre": centre,
        "gps": gps,
        "generated_at": datetime.now().isoformat(),
        "audit_hash": audit_hash,
        "summary": batch_stats,
        "policy_id": policy.get("policy_id", "default_v1"),
        "total_onions": len(results),
    }
    meta_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    # Generate HTML report
    html = _generate_html(
        report_id=report_id,
        batch_id=batch_id,
        farmer_id=farmer_id,
        officer_id=officer_id,
        centre=centre,
        policy=policy,
        batch_stats=batch_stats,
        results=results,
        gps=gps,
        annot_path=annot_path,
        orig_path=orig_path,
        qr_path=qr_path,
        audit_hash=audit_hash,
    )
    html_path = out_path / f"{report_id}.html"
    html_path.write_text(html, encoding="utf-8")

    # Generate PDF certificate
    pdf_path = out_path / f"{report_id}.pdf"
    _generate_pdf(
        path=pdf_path,
        report_id=report_id,
        batch_id=batch_id,
        farmer_id=farmer_id,
        officer_id=officer_id,
        centre=centre,
        gps=gps,
        batch_stats=batch_stats,
        results=results,
        annot_path=annot_path,
        qr_path=qr_path,
        audit_hash=audit_hash,
    )

    return report_id


def _generate_html(
    report_id: str,
    batch_id: str,
    farmer_id: str,
    officer_id: str,
    centre: str,
    policy: dict,
    batch_stats: dict,
    results: list[OnionResult],
    gps: Optional[Tuple[float, float]],
    annot_path: Path,
    orig_path: Path,
    qr_path: Path,
    audit_hash: str,
) -> str:
    gps_str = f"{gps[0]:.6f}, {gps[1]:.6f}" if gps else "N/A"
    verify_url = f"/reports/{report_id}/verify"

    rows = []
    for r in results:
        badge_color = {
            "GRADE_A": "#10b981",
            "GRADE_URS": "#f59e0b",
            "REJECTED": "#ef4444",
            "MANUAL_REVIEW": "#6366f1",
        }.get(r.final_grade, "#64748b")

        defects_list = [k for k, v in r.defects.__dict__.items() if v]
        defects_str = ", ".join(defects_list) if defects_list else "None"
        reasons = ", ".join(r.reason_codes) if r.reason_codes else "—"

        rows.append(f"""
            <tr>
              <td><strong>{r.onion_id}</strong></td>
              <td>{r.diameter_mm:.1f} mm</td>
              <td>{r.visual_class.replace('_', ' ').upper()}</td>
              <td>{defects_str}</td>
              <td>{r.confidence * 100:.1f}%</td>
              <td><span style="background: {badge_color}22; color: {badge_color}; border: 1px solid {badge_color}66; padding: 2px 8px; border-radius: 4px; font-weight: 600;">{r.final_grade}</span></td>
              <td style="font-size: 0.85em; color: #475569;">{reasons}</td>
            </tr>
        """)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Onion Grading Digital Certificate — {report_id}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 2rem; color: #0f172a; background: #f8fafc; }}
    .container {{ max-width: 960px; margin: 0 auto; background: #ffffff; padding: 2rem; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); border: 1px solid #e2e8f0; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #e2e8f0; padding-bottom: 1.5rem; margin-bottom: 1.5rem; }}
    .header h1 {{ color: #15803d; margin: 0 0 0.5rem 0; font-size: 1.6rem; }}
    .badge {{ display: inline-block; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; background: #dcfce7; color: #166534; }}
    .qr-box {{ text-align: center; }}
    .qr-box img {{ width: 110px; height: 110px; border: 1px solid #cbd5e1; border-radius: 6px; }}
    .meta-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; background: #f1f5f9; padding: 1rem; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.9rem; }}
    .meta-grid div strong {{ display: block; color: #64748b; font-size: 0.75rem; text-transform: uppercase; }}
    .kpi-row {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 0.75rem; margin-bottom: 1.5rem; }}
    .kpi-card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.8rem; text-align: center; }}
    .kpi-card .val {{ font-size: 1.4rem; font-weight: 800; color: #0f172a; }}
    .kpi-card .lbl {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; margin-top: 4px; }}
    .images-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1.5rem; }}
    .images-grid img {{ width: 100%; border-radius: 8px; border: 1px solid #cbd5e1; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e2e8f0; text-align: left; }}
    th {{ background: #f8fafc; font-weight: 600; color: #475569; }}
    .audit-footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; font-size: 0.75rem; color: #64748b; font-family: monospace; word-break: break-all; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <span class="badge">OFFICIAL APMC MANDI CERTIFICATE</span>
        <h1>Onion Quality Grading & Audit Report</h1>
        <p style="color: #64748b; margin: 0; font-size: 0.85rem;">Generated with YOLOv8s-Seg Instance Segmentation & ArUco Metric Calibration</p>
      </div>
      <div class="qr-box">
        <img src="/reports/{qr_path.name}" alt="Digital Audit Seal">
        <div style="font-size: 0.65rem; color: #64748b; margin-top: 4px;">Scannable Audit Seal</div>
      </div>
    </div>

    <div class="meta-grid">
      <div><strong>Report ID</strong>{report_id}</div>
      <div><strong>Batch Identifier</strong>{batch_id}</div>
      <div><strong>Farmer ID</strong>{farmer_id}</div>
      <div><strong>Procurement Centre</strong>{centre}</div>
      <div><strong>Inspecting Officer</strong>{officer_id}</div>
      <div><strong>GPS Location</strong>{gps_str}</div>
    </div>

    <div class="kpi-row">
      <div class="kpi-card"><div class="val">{batch_stats['total']}</div><div class="lbl">Total Onions</div></div>
      <div class="kpi-card"><div class="val" style="color: #10b981;">{batch_stats['grade_a_pct']}%</div><div class="lbl">Grade A</div></div>
      <div class="kpi-card"><div class="val" style="color: #f59e0b;">{batch_stats['grade_urs_pct']}%</div><div class="lbl">Grade URS</div></div>
      <div class="kpi-card"><div class="val" style="color: #ef4444;">{batch_stats['rejected_pct']}%</div><div class="lbl">Rejected</div></div>
      <div class="kpi-card"><div class="val" style="color: #6366f1;">{batch_stats.get('avg_diameter_mm', 0):.1f}mm</div><div class="lbl">Avg Diameter</div></div>
    </div>

    <div class="images-grid">
      <div>
        <h4 style="margin: 0 0 6px 0; color: #475569;">Original Capture</h4>
        <img src="/reports/{orig_path.name}" alt="Original Frame">
      </div>
      <div>
        <h4 style="margin: 0 0 6px 0; color: #475569;">Segmented Visual Evidence</h4>
        <img src="/reports/{annot_path.name}" alt="Annotated Frame">
      </div>
    </div>

    <h3 style="margin-top: 1.5rem; margin-bottom: 0.5rem; color: #1e293b;">Per-Onion Procurement Ledger</h3>
    <table>
      <thead>
        <tr><th>ID</th><th>Diameter</th><th>AI Visual</th><th>Defects</th><th>Confidence</th><th>Grade</th><th>Audit Reason Codes</th></tr>
      </thead>
      <tbody>
        {''.join(rows)}
      </tbody>
    </table>

    <div class="audit-footer">
      <strong>CRYPTOGRAPHIC SHA-256 AUDIT SEAL:</strong> {audit_hash}<br>
      Digital verification endpoint: {verify_url}
    </div>
  </div>
</body>
</html>"""


def _generate_pdf(
    path: Path,
    report_id: str,
    batch_id: str,
    farmer_id: str,
    officer_id: str,
    centre: str,
    gps: Optional[Tuple[float, float]],
    batch_stats: dict,
    results: list[OnionResult],
    annot_path: Path,
    qr_path: Path,
    audit_hash: str,
):
    """
    Generates a certified, clean multi-page PDF inspection certificate using ReportLab Platypus.
    """
    doc = SimpleDocTemplate(
        str(path),
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        "CertTitle",
        parent=styles["Heading1"],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#15803d"),
        spaceAfter=4,
    )
    sub_style = ParagraphStyle(
        "CertSub",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=12,
    )
    cell_style = ParagraphStyle(
        "CellNormal",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
    )
    cell_bold = ParagraphStyle(
        "CellBold",
        parent=styles["Normal"],
        fontSize=8,
        leading=10,
        fontName="Helvetica-Bold",
    )

    # Header with title and QR Code
    header_data = [
        [
            Paragraph("<b>APMC MANDI INSPECTION CERTIFICATE</b><br/><font size='14'><b>Onion Quality Grading & Audit Report</b></font><br/><font color='#64748b' size='8'>Trained YOLOv8s-Seg + ArUco Metric Calibration</font>", title_style),
            RLImage(str(qr_path), width=80, height=80),
        ]
    ]
    header_table = Table(header_data, colWidths=[440, 100])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))

    # Meta Details Table
    gps_text = f"{gps[0]:.4f}, {gps[1]:.4f}" if gps else "N/A"
    meta_data = [
        [
            Paragraph(f"<b>Report ID:</b> {report_id}", cell_style),
            Paragraph(f"<b>Batch ID:</b> {batch_id}", cell_style),
            Paragraph(f"<b>Farmer ID:</b> {farmer_id}", cell_style),
        ],
        [
            Paragraph(f"<b>Centre:</b> {centre}", cell_style),
            Paragraph(f"<b>Officer:</b> {officer_id}", cell_style),
            Paragraph(f"<b>GPS:</b> {gps_text}", cell_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[180, 180, 180])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # KPI Summary Row
    kpi_data = [
        [
            Paragraph(f"<b>Total</b><br/><font size='12'><b>{batch_stats['total']}</b></font>", cell_style),
            Paragraph(f"<b>Grade A</b><br/><font size='12' color='#10b981'><b>{batch_stats['grade_a_pct']}%</b></font>", cell_style),
            Paragraph(f"<b>Grade URS</b><br/><font size='12' color='#f59e0b'><b>{batch_stats['grade_urs_pct']}%</b></font>", cell_style),
            Paragraph(f"<b>Rejected</b><br/><font size='12' color='#ef4444'><b>{batch_stats['rejected_pct']}%</b></font>", cell_style),
            Paragraph(f"<b>Avg Size</b><br/><font size='12' color='#6366f1'><b>{batch_stats.get('avg_diameter_mm', 0):.1f}mm</b></font>", cell_style),
        ]
    ]
    kpi_table = Table(kpi_data, colWidths=[108, 108, 108, 108, 108])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # Scaled Annotated Evidence Image
    story.append(Paragraph("<b>Segmented Visual Evidence (Optical Calibration & Defect Masks)</b>", cell_bold))
    story.append(Spacer(1, 4))
    story.append(RLImage(str(annot_path), width=480, height=270))
    story.append(Spacer(1, 12))

    # Per-Onion Ledger Table
    ledger_data = [
        [
            Paragraph("<b>ID</b>", cell_bold),
            Paragraph("<b>Diameter</b>", cell_bold),
            Paragraph("<b>Defects</b>", cell_bold),
            Paragraph("<b>Conf</b>", cell_bold),
            Paragraph("<b>Grade</b>", cell_bold),
            Paragraph("<b>Reason Codes</b>", cell_bold),
        ]
    ]
    for r in results:
        defects_list = [k for k, v in r.defects.__dict__.items() if v]
        defects_str = ", ".join(defects_list) if defects_list else "None"
        reasons_str = ", ".join(r.reason_codes[:2]) if r.reason_codes else "—"

        ledger_data.append([
            Paragraph(r.onion_id, cell_style),
            Paragraph(f"{r.diameter_mm:.1f} mm", cell_style),
            Paragraph(defects_str, cell_style),
            Paragraph(f"{r.confidence * 100:.1f}%", cell_style),
            Paragraph(f"<b>{r.final_grade}</b>", cell_style),
            Paragraph(reasons_str, cell_style),
        ])

    ledger_table = Table(ledger_data, colWidths=[55, 75, 80, 50, 90, 190])
    ledger_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    story.append(ledger_table)
    story.append(Spacer(1, 10))

    # Audit Hash Footer
    hash_para = Paragraph(
        f"<b>SHA-256 DIGITAL AUDIT SEAL:</b> <font color='#475569'>{audit_hash}</font><br/>"
        f"<b>Digital Verification:</b> http://127.0.0.1:5000/reports/{report_id}/verify",
        ParagraphStyle("HashFoot", parent=styles["Normal"], fontSize=7, leading=9, fontName="Courier"),
    )
    story.append(hash_para)

    doc.build(story)
