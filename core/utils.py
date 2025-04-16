# core/utils.py
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
from io import BytesIO
from django.http import HttpResponse
import logging
from django.conf import settings
from twilio.rest import Client
from PyPDF2 import PdfWriter, PdfReader
from reportlab.lib.utils import ImageReader
from django.core.exceptions import ValidationError
from PIL import Image
import qrcode
# Initialize logger
logger = logging.getLogger(__name__)

def send_sms_notification(phone_number, message):
    client = Client(settings.TWILIO_SID, settings.TWILIO_TOKEN)
    
    try:
        client.messages.create(
            body=f"[TLS] {message}",
            from_=settings.TWILIO_NUMBER,
            to=phone_number
        )
        return True
    except Exception as e:
        logger.error(f"SMS failed: {str(e)}")
        return False


def validate_pdf(file):
    try:
        # Check first 4 bytes for PDF magic number
        if file.read(4) != b'%PDF':
            raise ValidationError("Not a valid PDF file")
        file.seek(0)
        
        # Full validation
        pdf = PdfReader(file)
        if len(pdf.pages) == 0:
            raise ValidationError("PDF contains no pages")
        return True
    except Exception as e:
        raise ValidationError(f"Corrupted PDF: {str(e)}")
    

def apply_stamp_to_pdf(pdf_data, stamp_image_path):
    # Generate QR code with a unique message (could be form data or UUID)
    qr = qrcode.QRCode(box_size=2, border=2)
    qr.add_data("Verified by Wakili System")  # You can customize this
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Load the original PDF
    original_pdf = PdfReader(io.BytesIO(pdf_data))
    output_pdf = PdfWriter()

    # Apply stamp and QR code to each page
    for page in original_pdf.pages:
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=letter)

        # Draw stamp image
        can.drawImage(stamp_image_path, 400, 50, width=120, height=60, mask='auto')

        # Save QR image to bytes and draw on canvas
        qr_bytes = io.BytesIO()
        qr_img.save(qr_bytes, format='PNG')
        qr_bytes.seek(0)
        can.drawImage(Image.open(qr_bytes), 50, 50, width=60, height=60)

        can.save()
        packet.seek(0)

        # Merge overlay with original
        overlay = PdfReader(packet)
        page.merge_page(overlay.pages[0])
        output_pdf.add_page(page)

    # Output the stamped PDF
    result = io.BytesIO()
    output_pdf.write(result)
    result.seek(0)
    return result