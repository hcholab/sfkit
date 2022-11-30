# sourcery skip: camel-case-classes, docstrings-for-classes, no-wildcard-imports, require-parameter-annotation, require-return-annotation, snake-case-functions
from io import BytesIO, StringIO

import pytest
from sfkit.encryption.mpc import encrypt_data, random_number_generator
from nacl.public import Box, PrivateKey, PublicKey
from tests.helper_functions_and_constants import *


def test_encrypt_GMP(mocker):
    # mock open
    mocker.patch("sfkit.encryption.mpc.encrypt_data.open", mock_open)
    # mock os.path.exists
    mocker.patch("sfkit.encryption.mpc.encrypt_data.os.path.exists", return_value=True)
    # mock os.makedirs
    mocker.patch("sfkit.encryption.mpc.encrypt_data.os.makedirs")
    # mock random_number_generator
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PseudoRandomNumberGenerator", mock_PseudoRandomNumberGenerator)

    encrypt_data.encrypt_GMP(mock_PseudoRandomNumberGenerator(), "input_dir")

    mocker.patch("sfkit.encryption.mpc.encrypt_data.os.path.exists", return_value=False)
    encrypt_data.encrypt_GMP(mock_PseudoRandomNumberGenerator(), "input_dir")


def test_get_shared_mpcgwas_keys(mocker):
    # mock Box
    mocker.patch("sfkit.encryption.mpc.encrypt_data.Box")
    # mock nacl.secret.SecretBox
    mocker.patch("sfkit.encryption.mpc.encrypt_data.nacl.secret.SecretBox", mock_SecretBox)

    # make random 32 byte string
    ran_bytes = bytes(list(range(32)))
    private_key = PrivateKey(ran_bytes)
    public_key = PublicKey(ran_bytes)
    encrypt_data.get_shared_mpcgwas_keys(private_key, public_key, False)
    encrypt_data.get_shared_mpcgwas_keys(private_key, public_key, True)


def test_encrypt_data(mocker):
    # mock get_user_email
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_user_email", return_value="a@a.com")
    # mock get_doc_ref_dict
    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_doc_ref_dict", return_value=mock_doc_ref_dict)
    # mock PublicKey
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PublicKey", return_value="public_key")
    # mock PrivateKey
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PrivateKey", return_value="private_key")
    # mock condition_or_fail
    mocker.patch("sfkit.encryption.mpc.encrypt_data.condition_or_fail")
    # mock get_shared_mpcgwas_keys
    mocker.patch(
        "sfkit.encryption.mpc.encrypt_data.get_shared_mpcgwas_keys",
        return_value=("shared_key", "shared_key", "shared_key", "shared_key"),
    )
    # mock open
    mocker.patch("sfkit.encryption.mpc.encrypt_data.open")
    # mock checksumdir.dirhash
    mocker.patch("sfkit.encryption.mpc.encrypt_data.checksumdir.dirhash", return_value="dirhash")
    # mock encrypt_GMP
    mocker.patch("sfkit.encryption.mpc.encrypt_data.encrypt_GMP")
    # mock shutil.copyfile
    mocker.patch("sfkit.encryption.mpc.encrypt_data.shutil.copyfile")
    # mock PseudoRandomNumberGenerator
    mocker.patch("sfkit.encryption.mpc.encrypt_data.PseudoRandomNumberGenerator")

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        encrypt_data.encrypt_data()

    mocker.patch("sfkit.encryption.mpc.encrypt_data.get_doc_ref_dict", return_value=mock_doc_ref_dict_keys)
    encrypt_data.encrypt_data()


def mock_open(path, mode):
    return StringIO("0\n1 2\n3 4 5") if mode == "r" else BytesIO()


class mock_PseudoRandomNumberGenerator:
    def __init__(self):
        pass

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
