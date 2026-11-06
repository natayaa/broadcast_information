"""Static catalogues shared by forms, validation and the mailer."""

from __future__ import annotations

DOCUMENT_TYPES: tuple[str, ...] = (
    "New Model Authorization",
    "New Model Information",
    "Part Evaluation",
    "ECN",
    "Technical report",
    "Study Report",
    "Mechanical Part Inspection Report",
    "Drop Test Report",
    "Vibration Test Report",
    "Part Injection Approval",
    "General Inspection Report",
    "TV Check Sheets",
    "Home Theater Check Sheet",
    "MM Part List",
    "MM Assembly 1",
    "MM Assembly 2",
    "MM Alignment/Adjustment",
    "Trial Run Evaluation",
    "New Model Trial Review",
    "FDRM",
    "Modification Information",
    "Approval Spec",
    "Approval Letter",
    "Other",
)

DIVISIONS: tuple[str, ...] = (
    "Production Engineer",
    "Production",
    "QC Line",
    "PQA",
    "Procurement",
    "Service",
    "QRCC",
    "Marketing",
    "Accounting",
    "Costing",
    "Promotion",
    "PPC",
    "CMC",
    "Production Planning",
    "TV Director",
)

RECIPIENT_CATEGORIES: tuple[str, ...] = ("Direct", "CC")

SMTP_SERVER_LABELS: dict[str, str] = {
    "sharp": "Internal SHARP Relay Server",
    "office": "International Common Server (Office 365)",
}
