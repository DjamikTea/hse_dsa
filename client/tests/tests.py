import pytest
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath("./client/hseclient"))
print(SCRIPT_DIR)
sys.path.append(os.path.dirname(SCRIPT_DIR))
from unittest.mock import Mock, patch
from datetime import datetime, timezone
from hseclient.content.crypt import (
    generate_csr,
    check_csr_root,
    sign_document,
    check_document,
)


class MockGostDSA:
    def sign(self, data, private_key):
        return f"signature_{private_key}"

    def check(self, signature, data, public_key):
        return signature == f"signature_{public_key}"


@pytest.fixture
def mock_gost_dsa():
    with patch("hsecrypto.GostDSA", return_value=MockGostDSA()):
        yield


@pytest.fixture
def sample_keys():
    return {
        "private_key": "a58e178fd3559a4604e79d1e2f03e5b752070ba089e0184669c459908519ceb8",
        "public_key": "a58e178fd3559a4604e79d1e2f03e5b752070ba089e0184669c459908519ceb8",
        "server_pubkey": "server_public",
    }


@pytest.fixture
def sample_csr(sample_keys):
    return generate_csr(
        private_key=sample_keys["private_key"],
        public_key=sample_keys["public_key"],
        country="RU",
        organization="TestOrg",
        phone_number="+79999999999",
        ip="127.0.0.1",
        fio="Ivan Ivanov",
    )


def test_generate_csr(mock_gost_dsa, sample_keys):
    csr = generate_csr(
        private_key=sample_keys["private_key"],
        public_key=sample_keys["public_key"],
        country="RU",
        organization="TestOrg",
        phone_number="+79999999999",
        ip="127.0.0.1",
        fio="Ivan Ivanov",
    )
    assert csr["client"]["public_key"] == sample_keys["public_key"]
    assert "client_sign" in csr
    assert "date_generation" in csr["client"]


def test_check_csr_root_valid_negative(mock_gost_dsa, sample_csr):
    sample_csr["root"] = {
        "root_ca": {
            "public_key": "a58e178fd3559a4604e79d1e2f03e5b752070ba089e0184669c459908519ceb8",
            "domain": "example.com",
        },
        "root_sign": "013123123".zfill(64),
    }
    result = check_csr_root(
        sample_csr, server_domain="example.com", server_pubkey="server_public"
    )
    assert result is not True


def test_check_csr_root_invalid_pubkey(mock_gost_dsa, sample_csr):
    sample_csr["root"] = {
        "root_ca": {
            "public_key": "013123123".zfill(64),
            "domain": "example.com",
        },
        "root_sign": "013123123".zfill(64),
    }
    result = check_csr_root(
        sample_csr, server_domain="example.com", server_pubkey="server_public"
    )
    assert result is False


def test_sign_document(mock_gost_dsa, sample_keys):
    timeuuid = "uuid123"
    sha256 = "hash123"
    certificate = "cert123"

    signed_doc = sign_document(
        timeuuid=timeuuid,
        sha256=sha256,
        private_key=sample_keys["private_key"],
        certificate=certificate,
    )

    assert signed_doc["timeuuid"] == timeuuid
    assert signed_doc["sha256"] == sha256
    assert signed_doc["cert"] == certificate
    assert "sign" in signed_doc


import pytest
from hseclient.content.crypt import (
    generate_csr,
    check_csr_root,
    sign_document,
)


def test_generate_csr_missing_key(mock_gost_dsa):
    """Test generate_csr raises ValueError for missing private_key."""
    with pytest.raises(TypeError):
        generate_csr(
            private_key=None,
            public_key="valid_pubkey",
            country="RU",
            organization="TestOrg",
            phone_number="+79999999999",
            ip="127.0.0.1",
            fio="Ivan Ivanov",
        )


def test_check_csr_root_missing_root(mock_gost_dsa, sample_csr):
    """Test check_csr_root raises KeyError if root_ca is missing."""
    sample_csr.update({"root": "root"})
    del sample_csr["root"]
    with pytest.raises(KeyError):
        check_csr_root(
            sample_csr, server_domain="example.com", server_pubkey="server_public"
        )


def test_sign_document_empty_private_key(mock_gost_dsa):
    """Test sign_document raises ValueError for an empty private_key."""
    with pytest.raises(ValueError):
        sign_document(
            timeuuid="uuid123",
            sha256="hash123",
            private_key="",
            certificate="cert1234",
        )
