# vipaccess/qr.py
"""QR code generation with intelligent fallback."""

import subprocess
import sys
from typing import Optional


def generate_qr_code(data: str, invert: bool = True) -> bool:
    """
    Generate QR code with intelligent fallback.

    Priority:
    1. qrcode library (if installed)
    2. qrencode command line tool (if available)
    3. Plain text output (fallback)

    Args:
        data: The data to encode in QR code
        invert: Whether to invert colors (for terminal display)

    Returns:
        True if QR code was displayed, False if fallback was used
    """
    # Priority 1: Try qrcode library
    try:
        import qrcode
        qr = qrcode.QRCode(
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            border=1
        )
        qr.add_data(data)
        qr.print_ascii(invert=invert)
        return True
    except (ImportError, UnicodeEncodeError):
        pass

    # Priority 2: Try qrencode command line tool
    try:
        result = subprocess.run(
            ['qrencode', '-t', 'UTF8', data],
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass

    # Priority 3: Plain text fallback
    print(f"QR Code URI: {data}")
    print("Install 'qrcode' or 'qrencode' to display QR codes")
    return False
