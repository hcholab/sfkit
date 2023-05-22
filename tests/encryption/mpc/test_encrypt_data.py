# sourcery skip: camel-case-classes, no-wildcard-imports, snake-case-functions
from io import BytesIO, StringIO
from typing import Callable, Generator

import pytest
from nacl.public import PrivateKey, PublicKey
from pytest_mock import MockerFixture

from sfkit.encryption.mpc import encrypt_data
from tests.helper_functions_and_constants import *


def test_encrypt_GMP(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.encryption.mpc.encrypt_data.open", mock_open)
    mocker.patch("sfkit.encryption.mpc.encrypt_data.os.path.exists", return_value=True)
    mocker.patch("sfkit.encryption.mpc.encrypt_data.os.makedirs")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PseudoRandomNumberGenerator", mock_PseudoRandomNumberGenerator)

    encrypt_data.encrypt_GMP(mock_PseudoRandomNumberGenerator(), "input_dir", "output_dir")  # type: ignore

    mocker.patch("sfkit.encryption.mpc.encrypt_data.os.path.exists", return_value=False)
    encrypt_data.encrypt_GMP(mock_PseudoRandomNumberGenerator(), "input_dir", "output_dir")  # type: ignore


def test_get_shared_mpcgwas_keys(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.encryption.mpc.encrypt_data.Box")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.nacl.secret.SecretBox", mock_SecretBox)

    # make random 32 byte string
    ran_bytes = bytes(list(range(32)))
    private_key = PrivateKey(ran_bytes)
    public_key = PublicKey(ran_bytes)
    encrypt_data.get_shared_mpcgwas_keys(private_key, public_key, False)
    encrypt_data.get_shared_mpcgwas_keys(private_key, public_key, True)


def test_encrypt_data(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_username", return_value="a@a.com")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_doc_ref_dict", return_value=mock_doc_ref_dict)
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_other_user_public_key")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PublicKey", return_value="public_key")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PrivateKey", return_value="private_key")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.condition_or_fail")
    mocker.patch(
        "sfkit.encryption.mpc.encrypt_data.get_shared_mpcgwas_keys",
        return_value=("shared_key", "shared_key", "shared_key", "shared_key"),
    )
    mocker.patch("sfkit.encryption.mpc.encrypt_data.open")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.checksumdir.dirhash", return_value="dirhash")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.encrypt_GMP")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.shutil.copyfile")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PseudoRandomNumberGenerator")

    encrypt_data.encrypt_data()


def test_get_other_user_public_key(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    # Mock functions
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_doc_ref_dict")
    mocker.patch("sfkit.encryption.mpc.encrypt_data.time.sleep")

    mock_doc_ref_dict = {
        "participants": ["Broad", "user1@example.com", "user2@example.com"],
        "personal_parameters": {
            "Broad": {"PUBLIC_KEY": {"value": "Broad_public_key"}},
            "user1@example.com": {"PUBLIC_KEY": {"value": "user1_public_key"}},
            "user2@example.com": {"PUBLIC_KEY": {"value": "user2_public_key"}},
        },
    }
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_doc_ref_dict", return_value=mock_doc_ref_dict)

    # Test valid case for role 1
    result = encrypt_data.get_other_user_public_key(mock_doc_ref_dict, 1)
    assert result == "user2_public_key"

    # Test valid case for role 2
    result = encrypt_data.get_other_user_public_key(mock_doc_ref_dict, 2)
    assert result == "user1_public_key"

    mock_doc_ref_dict["personal_parameters"]["user2@example.com"]["PUBLIC_KEY"]["value"] = None
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_doc_ref_dict", return_value=mock_doc_ref_dict)

    def mock_sleep(*args, **kwargs):
        mock_doc_ref_dict["personal_parameters"]["user2@example.com"]["PUBLIC_KEY"]["value"] = "user2_public_key"

    mocker.patch("sfkit.encryption.mpc.encrypt_data.time.sleep", side_effect=mock_sleep)

    result = encrypt_data.get_other_user_public_key(mock_doc_ref_dict, 1)
    assert result == "user2_public_key"

    # Test timeout waiting for public key
    mock_doc_ref_dict["personal_parameters"]["user2@example.com"]["PUBLIC_KEY"]["value"] = None
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_doc_ref_dict", return_value=mock_doc_ref_dict)
    mocker.patch("sfkit.encryption.mpc.encrypt_data.time.sleep", side_effect=lambda x: None)

    with pytest.raises(SystemExit):
        encrypt_data.get_other_user_public_key(mock_doc_ref_dict, 1)

    # Test invalid number of participants
    mock_doc_ref_dict["participants"].pop()
    with pytest.raises(SystemExit):
        encrypt_data.get_other_user_public_key(mock_doc_ref_dict, 1)


def mock_open(path, mode):
    return StringIO("0\n1 2\n3 \n3\n3\n3\n3\n3\n3\n3\n3\n3\n3\n3\n3\n3\n4 5") if mode == "r" else BytesIO()


class mock_PseudoRandomNumberGenerator:
    def __init__(self):
        self.base_p = 2

    def next(self):
        return 1


class mock_SecretBox:
    def __init__(self, key):
        pass

    def encrypt(self, message, nonce):
        return MockEncryptedMessage(message)


class MockEncryptedMessage:
    def __init__(self, message):
        self.message = message
        self.ciphertext = message
