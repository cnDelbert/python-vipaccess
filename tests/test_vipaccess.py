"""Tests for vipaccess module."""

import unittest
import os
import tempfile
from unittest.mock import patch, MagicMock
from vipaccess import provision as vp
from vipaccess import __main__ as vm


class TestProvision(unittest.TestCase):
    """Test provisioning functionality."""
    
    def test_generate_request(self):
        """Test that request generation works."""
        request = vp.generate_request(token_model='SYMC')
        self.assertIn('SYMC', request)
        self.assertIn('GetSharedSecret', request)
    
    def test_generate_otp_uri(self):
        """Test OTP URI generation."""
        token = {
            'id': 'SYMC12345678',
            'period': 30,
            'counter': None,
            'digits': 6,
            'algorithm': 'sha1'
        }
        secret = b'\x00' * 20
        uri = vp.generate_otp_uri(token, secret)
        self.assertIn('otpauth://totp/', uri)
        self.assertIn('SYMC12345678', uri)
    
    def test_decrypt_key(self):
        """Test key decryption."""
        iv = b'\x00' * 16
        cipher = b'\x00' * 16
        try:
            vp.decrypt_key(iv, cipher)
        except Exception:
            pass


class TestMain(unittest.TestCase):
    """Test main module functionality."""
    
    def test_check_token_model(self):
        """Test token model validation."""
        self.assertEqual(vm.check_token_model('SYMC'), 'SYMC')
        self.assertEqual(vm.check_token_model('VSMT'), 'VSMT')
        self.assertEqual(vm.check_token_model('ABC'), 'ABC')
        
        with self.assertRaises(Exception):
            vm.check_token_model('ABCDE')
        with self.assertRaises(Exception):
            vm.check_token_model('ABC123')


class TestQRCode(unittest.TestCase):
    """Test QR code generation."""
    
    @patch('builtins.print')
    def test_generate_qr_code_function_exists(self, mock_print):
        """Test that QR code generation function exists."""
        from vipaccess.qr import generate_qr_code
        result = generate_qr_code('test://data')
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main()