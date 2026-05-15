# -*- coding: utf-8 -*-
#
#   Copyright 2015 Forest Crossman
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


import unittest
import os
from urllib import parse as urlparse
from time import sleep
from warnings import warn

import requests

from vipaccess.provision import (
    generate_request,
    get_token_from_response,
    decrypt_key,
    generate_otp_uri,
    check_token,
    sync_token,
    VIP_ACCESS_LOGO,
    PROVISIONING_URL,
)

# Network tests are slow and unreliable, so skip by default
# Set RUN_NETWORK_TESTS=true to enable them
RUN_NETWORK_TESTS = os.getenv("RUN_NETWORK_TESTS", "").lower() in ("true", "1", "yes")


def test_generate_request():
    expected = (
        '<?xml version="1.0" encoding="UTF-8" ?>\n'
        '<GetSharedSecret Id="1412030064" Version="2.0"\n'
        '    xmlns="http://www.verisign.com/2006/08/vipservice"\n'
        '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        "    <TokenModel>SYMC</TokenModel>\n"
        "    <ActivationCode></ActivationCode>\n"
        '    <OtpAlgorithm type="HMAC-SHA1-TRUNC-6DIGITS"/>\n'
        "    <SharedSecretDeliveryMethod>HTTPS</SharedSecretDeliveryMethod>\n"
        '    <Extension extVersion="auth" xsi:type="vip:ProvisionInfoType"\n'
        '        xmlns:vip="http://www.verisign.com/2006/08/vipservice">\n'
        "        <AppHandle>iMac010200</AppHandle>\n"
        "        <ClientIDType>BOARDID</ClientIDType>\n"
        "        <ClientID>python-vipaccess-X.Y.Z</ClientID>\n"
        "        <DistChannel>Symantec</DistChannel>\n"
        "        <ClientTimestamp>1412030064</ClientTimestamp>\n"
        "        <Data>MyvXiv5vU27qBbRDN2HwbVAp0n+e67QWfWhXlbPb4Q8=</Data>\n"
        "    </Extension>\n"
        "</GetSharedSecret>"
    )
    params = {
        "timestamp": 1412030064,
        "token_model": "SYMC",
        "otp_algorithm": "HMAC-SHA1-TRUNC-6DIGITS",
        "shared_secret_delivery_method": "HTTPS",
        "app_handle": "iMac010200",
        "client_id_type": "BOARDID",
        "client_id": "python-vipaccess-X.Y.Z",
        "dist_channel": "Symantec",
    }
    request = generate_request(**params)
    assert expected == request


def test_get_token_from_response():
    test_response = (
        b'<?xml version="1.0" encoding="UTF-8"?>\n'
        b'<GetSharedSecretResponse RequestId="1412030064" Version="2.0" '
        b'xmlns="http://www.verisign.com/2006/08/vipservice">\n'
        b"  <Status>\n"
        b"    <ReasonCode>0000</ReasonCode>\n"
        b"    <StatusMessage>Success</StatusMessage>\n"
        b"  </Status>\n"
        b"  <SharedSecretDeliveryMethod>HTTPS</SharedSecretDeliveryMethod>\n"
        b'  <SecretContainer Version="1.0">\n'
        b"    <EncryptionMethod>\n"
        b"      <PBESalt>u5lgf1Ek8WA0iiIwVkjy26j6pfk=</PBESalt>\n"
        b"      <PBEIterationCount>50</PBEIterationCount>\n"
        b"      <IV>Fsg1KafmAX80gUEDADijHw==</IV>\n"
        b"    </EncryptionMethod>\n"
        b"    <Device>\n"
        b'      <Secret type="HOTP" Id="SYMC26070843">\n'
        b"        <Issuer>OU = ID Protection Center, O = VeriSign, Inc.</Issuer>\n"
        b'        <Usage otp="true">\n'
        b'          <AI type="HMAC-SHA1-TRUNC-6DIGITS"/>\n'
        b"          <TimeStep>30</TimeStep>\n"
        b"          <Time>0</Time>\n"
        b"          <ClockDrift>4</ClockDrift>\n"
        b"        </Usage>\n"
        b"        <FriendlyName>OU = ID Protection Center, O = VeriSign, Inc.</FriendlyName>\n"
        b"        <Data>\n"
        b"          <Cipher>ILBweOCEOoMBLJARzoeUIlu0+5m6b3khZljd5dozARk=</Cipher>\n"
        b'          <Digest algorithm="HMAC-SHA1">MoaidW7XDzeTZJqhfRQCZEieARM=</Digest>\n'
        b"        </Data>\n"
        b"        <Expiry>2017-09-25T23:36:22.056Z</Expiry>\n"
        b"      </Secret>\n"
        b"    </Device>\n"
        b"  </SecretContainer>\n"
        b"  <UTCTimestamp>1412030065</UTCTimestamp>\n"
        b"</GetSharedSecretResponse>"
    )
    expected_token = {
        "salt": b'\xbb\x99`\x7fQ$\xf1`4\x8a"0VH\xf2\xdb\xa8\xfa\xa5\xf9',
        "iteration_count": 50,
        "iv": b"\x16\xc85)\xa7\xe6\x01\x7f4\x81A\x03\x008\xa3\x1f",
        "id": "SYMC26070843",
        "cipher": b' \xb0px\xe0\x84:\x83\x01,\x90\x11\xce\x87\x94"[\xb4\xfb\x99\xbaoy!fX\xdd\xe5\xda3\x01\x19',
        "digest": b"2\x86\xa2un\xd7\x0f7\x93d\x9a\xa1}\x14\x02dH\x9e\x01\x13",
        "expiry": "2017-09-25T23:36:22.056Z",
        "period": 30,
        "algorithm": "sha1",
        "digits": 6,
        "counter": None,
    }
    token = get_token_from_response(test_response)
    assert token.pop("timeskew", None) is not None
    assert expected_token == token


def test_decrypt_key():
    test_iv = b"\x16\xc85)\xa7\xe6\x01\x7f4\x81A\x03\x008\xa3\x1f"
    test_cipher = b' \xb0px\xe0\x84:\x83\x01,\x90\x11\xce\x87\x94"[\xb4\xfb\x99\xbaoy!fX\xdd\xe5\xda3\x01\x19'
    expected_key = b'ZqeD\xd9wg]"\x12\x1f7\xc7v6"\xf0\x13\\i'
    decrypted_key = decrypt_key(test_iv, test_cipher)
    assert expected_key == decrypted_key


def test_generate_totp_uri():
    test_token = {
        "salt": b'\xbb\x99`\x7fQ$\xf1`4\x8a"0VH\xf2\xdb\xa8\xfa\xa5\xf9',
        "iteration_count": 50,
        "iv": b"\x16\xc85)\xa7\xe6\x01\x7f4\x81A\x03\x008\xa3\x1f",
        "id": "SYMC26070843",
        "cipher": b' \xb0px\xe0\x84:\x83\x01,\x90\x11\xce\x87\x94"[\xb4\xfb\x99\xbaoy!fX\xdd\xe5\xda3\x01\x19',
        "digest": b"2\x86\xa2un\xd7\x0f7\x93d\x9a\xa1}\x14\x02dH\x9e\x01\x13",
        "expiry": "2017-09-25T23:36:22.056Z",
        "counter": None,
        "period": 30,
        "algorithm": "sha1",
        "digits": 6,
        "timeskew": 0,
    }
    test_secret = b'ZqeD\xd9wg]"\x12\x1f7\xc7v6"\xf0\x13\\i'
    expected_uri = urlparse.urlparse(
        "otpauth://totp/VIP%20Access:SYMC26070843?secret=LJYWKRGZO5TV2IQSD434O5RWELYBGXDJ&image=" + VIP_ACCESS_LOGO
    )
    generated_uri = urlparse.urlparse(generate_otp_uri(test_token, test_secret))
    assert expected_uri.scheme == generated_uri.scheme
    assert expected_uri.netloc == generated_uri.netloc
    assert expected_uri.path == generated_uri.path
    assert urlparse.parse_qs(expected_uri.params) == urlparse.parse_qs(generated_uri.params)
    assert urlparse.parse_qs(expected_uri.query) == urlparse.parse_qs(generated_uri.query)


def test_generate_hotp_uri():
    test_token = {
        "salt": b"1\x92\xef\xb5\x99\xaf\xa9\xe3)\x17\xaf \x9b\xa5\x95j7\xe7\xa9+",
        "iteration_count": 50,
        "iv": b"Q\xf6I\xb3\xc9!\xfd3\xc64\x8ae\x83\x8d\x9c\xaf",
        "id": "UBHE57586348",
        "cipher": b"!\x90)]e\x12\xe6\xcf\xa9\xd3\xa7\xaf\xdf\xb0\x89\x1f~\xe6\x17\xe7'\xd7pU\xcd>x\xf7\xc1\xc22\xe1",
        "digest": b"\xc3sA\xe9\x02\\\xff\x02m\x1d\xb5i\x1a\xb7\xdc\x85&yl\xcd",
        "expiry": "2022-06-03T07:21:46.825Z",
        "period": None,
        "counter": 1,
        "algorithm": "sha1",
        "digits": 6,
        "timeskew": 0,
    }
    test_secret = b"\x9a\x13\xcd2!\xad\xbd\x97R\xfcEE\xb6\x92e\xb4\x14\xb0\xfem"
    expected_uri = urlparse.urlparse(
        "otpauth://hotp/VIP%20Access:UBHE57586348?counter=1&secret=TIJ42MRBVW6ZOUX4IVC3NETFWQKLB7TN&image=" + VIP_ACCESS_LOGO
    )
    generated_uri = urlparse.urlparse(generate_otp_uri(test_token, test_secret))
    assert expected_uri.scheme == generated_uri.scheme
    assert expected_uri.netloc == generated_uri.netloc
    assert expected_uri.path == generated_uri.path
    assert urlparse.parse_qs(expected_uri.params) == urlparse.parse_qs(generated_uri.params)
    assert urlparse.parse_qs(expected_uri.query) == urlparse.parse_qs(generated_uri.query)


def provision_valid_token(token_model, attr, not_attr, check_sync=False):
    test_request = generate_request(token_model=token_model)
    test_response = requests.post(PROVISIONING_URL, data=test_request)
    test_otp_token = get_token_from_response(test_response.content)
    assert test_otp_token[attr] is not None
    assert test_otp_token[not_attr] is None
    assert test_otp_token["id"].startswith(token_model)
    test_token_secret = decrypt_key(test_otp_token["iv"], test_otp_token["cipher"])
    assert check_token(test_otp_token, test_token_secret)
    if check_sync:
        if test_otp_token["period"] is not None:
            warn("Test is still running. Need to sleep for {}s to check token sync...".format(2 * test_otp_token["period"]))
            sleep(2 * test_otp_token["period"])
        assert sync_token(test_otp_token, test_token_secret)


class TestTokenModels(unittest.TestCase):
    """Test cases for different token models using subTest for parameterization."""

    @unittest.skipUnless(RUN_NETWORK_TESTS, "Network tests are slow and unreliable. Set RUN_NETWORK_TESTS=true to enable.")
    def test_check_TOTP_token_models(self):
        """Test TOTP token models: VSMT, VSST, SYMC, SYDC."""
        # Only try syncing one TOTP token, because it requires a delay.
        token_models = ("VSMT", "VSST", "SYMC", "SYDC")
        for i, token_model in enumerate(token_models):
            with self.subTest(token_model=token_model):
                # First token doesn't need sync, others do
                check_sync = i > 0
                if i > 0:
                    # Tests fail without this delay
                    sleep(3)
                provision_valid_token(token_model, "period", "counter", check_sync)

    @unittest.skipUnless(RUN_NETWORK_TESTS, "Network tests are slow and unreliable. Set RUN_NETWORK_TESTS=true to enable.")
    def test_check_HOTP_token_models(self):
        """Test HOTP token models: UBHE."""
        token_models = ("UBHE",)
        for token_model in token_models:
            with self.subTest(token_model=token_model):
                provision_valid_token(token_model, "counter", "period", True)

    @unittest.skipUnless(RUN_NETWORK_TESTS, "Network tests are slow and unreliable. Set RUN_NETWORK_TESTS=true to enable.")
    def test_check_token_detects_invalid_token(self):
        """Test that check_token correctly detects invalid tokens."""
        test_token = {"id": "SYMC26070843", "period": 30}
        test_token_secret = b'ZqeD\xd9wg]"\x12\x1f7\xc7v6"\xf0\x13\\i'
        self.assertFalse(check_token(test_token, test_token_secret))


if __name__ == "__main__":
    unittest.main()
