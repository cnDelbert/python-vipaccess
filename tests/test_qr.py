"""Tests for QR code generation with fallback."""

import sys
import unittest
from unittest.mock import patch, MagicMock
from vipaccess import qr
from vipaccess.qr import generate_qr_code


class TestQRCodeFallback(unittest.TestCase):
    """Test QR code generation fallback mechanism."""

    def tearDown(self):
        # Clean up any patches that might have been applied to sys.modules
        if "qrcode" in sys.modules:
            del sys.modules["qrcode"]

    @patch("builtins.print")
    def test_qrcode_library_success(self, mock_print):
        """Test that qrcode library is used when available."""
        # Create a complete mock qrcode module
        mock_qr_instance = MagicMock()
        mock_qr_instance.print_ascii.return_value = None

        mock_qrcode_module = MagicMock()
        mock_qrcode_module.QRCode.return_value = mock_qr_instance
        mock_qrcode_module.constants.ERROR_CORRECT_L = 0

        # Patch the module-level import in qr.py
        with patch.dict(sys.modules, {"qrcode": mock_qrcode_module}):
            # Reload the qr module to pick up the mock
            import importlib

            importlib.reload(qr)
            from vipaccess.qr import generate_qr_code as new_generate_qr_code

            result = new_generate_qr_code("otpauth://totp/test:test?secret=AAA")

        self.assertTrue(result)
        mock_qr_instance.add_data.assert_called_once_with("otpauth://totp/test:test?secret=AAA")
        mock_qr_instance.print_ascii.assert_called_once_with(invert=True)

    @patch("builtins.print")
    @patch("subprocess.run")
    def test_qrcode_unicode_error_fallback_to_qrencode(self, mock_subprocess_run, mock_print):
        """Test that qrencode is used when qrcode library raises UnicodeEncodeError."""
        # Create a mock qrcode module that raises UnicodeEncodeError on print_ascii
        mock_qr_instance = MagicMock()
        mock_qr_instance.print_ascii.side_effect = UnicodeEncodeError("gbk", "\u2580", 0, 1, "illegal multibyte sequence")

        mock_qrcode_module = MagicMock()
        mock_qrcode_module.QRCode.return_value = mock_qr_instance
        mock_qrcode_module.constants.ERROR_CORRECT_L = 0

        # Make qrencode succeed
        mock_result = MagicMock()
        mock_result.stdout = "QR code output"
        mock_subprocess_run.return_value = mock_result

        # Patch the module-level import in qr.py
        with patch.dict(sys.modules, {"qrcode": mock_qrcode_module}):
            # Reload the qr module to pick up the mock
            import importlib

            importlib.reload(qr)
            from vipaccess.qr import generate_qr_code as new_generate_qr_code

            result = new_generate_qr_code("otpauth://totp/test:test?secret=AAA")

        self.assertTrue(result)
        mock_subprocess_run.assert_called_once_with(
            ["qrencode", "-t", "UTF8", "otpauth://totp/test:test?secret=AAA"], capture_output=True, text=True, check=True
        )

    @patch("builtins.print")
    @patch("subprocess.run")
    @patch("builtins.__import__")
    def test_qrcode_import_error_fallback_to_qrencode(self, mock_import, mock_subprocess_run, mock_print):
        """Test that qrencode is used when qrcode library is not available."""

        # Make qrcode import fail
        def import_side_effect(name, *args, **kwargs):
            if name == "qrcode":
                raise ImportError("qrcode not found")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect

        # Make qrencode succeed
        mock_result = MagicMock()
        mock_result.stdout = "QR code output"
        mock_subprocess_run.return_value = mock_result

        result = generate_qr_code("otpauth://totp/test:test?secret=AAA")

        self.assertTrue(result)
        mock_subprocess_run.assert_called_once_with(
            ["qrencode", "-t", "UTF8", "otpauth://totp/test:test?secret=AAA"], capture_output=True, text=True, check=True
        )

    @patch("builtins.print")
    @patch("subprocess.run")
    @patch("builtins.__import__")
    def test_plain_text_fallback(self, mock_import, mock_subprocess_run, mock_print):
        """Test that plain text is used when both qrcode and qrencode are unavailable."""

        # Make qrcode import fail
        def import_side_effect(name, *args, **kwargs):
            if name == "qrcode":
                raise ImportError("qrcode not found")
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = import_side_effect

        # Make qrencode fail
        mock_subprocess_run.side_effect = FileNotFoundError

        result = generate_qr_code("otpauth://totp/test:test?secret=AAA")

        self.assertFalse(result)
        mock_print.assert_any_call("QR Code URI: otpauth://totp/test:test?secret=AAA")
        mock_print.assert_any_call("Install 'qrcode' or 'qrencode' to display QR codes")


if __name__ == "__main__":
    unittest.main()
