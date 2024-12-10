import pytest

import hsecrypto


@pytest.fixture
def dsa():
    return hsecrypto.GostDSA()


@pytest.fixture
def keys(dsa: hsecrypto.GostDSA):
    private_key, public_key = dsa.generate_key_pair()
    return private_key, public_key


def test_sign_and_verify(dsa: hsecrypto.GostDSA, keys: tuple[str, str]):
    private_key, public_key = keys
    signature = dsa.sign(b"test", private_key=private_key)

    result = dsa.check(signature=signature, message=b"test", public_key=public_key)

    assert result is True


def test_sign_and_verify_negative(dsa: hsecrypto.GostDSA, keys: tuple[str, str]):
    private_key, public_key = keys
    signature = dsa.sign(b"test1", private_key=private_key)

    result = dsa.check(signature=signature, message=b"test", public_key=public_key)

    assert result is False
