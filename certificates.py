import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


def generate_certificate_code():
    return f"DB-{uuid.uuid4().hex[:10].upper()}"


def generate_certificate_pdf(output_folder, username, category_name, cert_code, bites_completed):
    """Generates a polished landscape PDF certificate using ReportLab."""
    os.makedirs(output_folder, exist_ok=True)
    filename = f"certificate_{cert_code}.pdf"
    filepath = os.path.join(output_folder, filename)

    page_size = landscape(A4)
    c = canvas.Canvas(filepath, pagesize=page_size)
    width, height = page_size

    # Background
    c.setFillColor(colors.HexColor("#0f172a"))
    c.rect(0, 0, width, height, fill=1, stroke=0)

    # Inner card
    margin = 18 * mm
    c.setFillColor(colors.white)
    c.roundRect(margin, margin, width - 2 * margin, height - 2 * margin, 8, fill=1, stroke=0)

    # Decorative border
    c.setStrokeColor(colors.HexColor("#6366f1"))
    c.setLineWidth(3)
    c.roundRect(margin + 6, margin + 6, width - 2 * margin - 12, height - 2 * margin - 12, 6, fill=0, stroke=1)

    # Header
    c.setFillColor(colors.HexColor("#6366f1"))
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, height - margin - 28, "DEVBITES")
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.HexColor("#64748b"))
    c.drawCentredString(width / 2, height - margin - 42, "MICRO-LEARNING FOR DEVELOPERS")

    # Title
    c.setFillColor(colors.HexColor("#0f172a"))
    c.setFont("Helvetica-Bold", 30)
    c.drawCentredString(width / 2, height - margin - 80, "Certificate of Completion")

    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#334155"))
    c.drawCentredString(width / 2, height - margin - 110, "This certificate is proudly presented to")

    c.setFont("Helvetica-Bold", 26)
    c.setFillColor(colors.HexColor("#6366f1"))
    c.drawCentredString(width / 2, height - margin - 145, username)

    c.setFont("Helvetica", 13)
    c.setFillColor(colors.HexColor("#334155"))
    text = f"for successfully completing {bites_completed} bites in the {category_name} learning track"
    c.drawCentredString(width / 2, height - margin - 175, text)

    # Date and code
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.HexColor("#64748b"))
    issued = datetime.utcnow().strftime("%B %d, %Y")
    c.drawString(margin + 30, margin + 30, f"Issued: {issued}")
    c.drawRightString(width - margin - 30, margin + 30, f"Certificate ID: {cert_code}")

    # Signature line
    c.setStrokeColor(colors.HexColor("#94a3b8"))
    c.setLineWidth(1)
    c.line(width / 2 - 70, margin + 55, width / 2 + 70, margin + 55)
    c.setFont("Helvetica-Oblique", 10)
    c.drawCentredString(width / 2, margin + 42, "DevBites Learning Platform")

    c.showPage()
    c.save()
    return filepath, filename
