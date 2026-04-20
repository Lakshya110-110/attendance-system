"""
qr_service.py - Generate QR codes for attendance sessions
Returns base64-encoded PNG strings ready for display in browser / Streamlit.
"""

import qrcode
import base64
from io import BytesIO


def generate_qr(session_id: str) -> str:
    """
    Encode session_id into a QR code and return as a base64 PNG string.
    """
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(session_id)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0f172a", back_color="white")

    buffer = BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    encoded = base64.b64encode(buffer.read()).decode("utf-8")
    return encoded
