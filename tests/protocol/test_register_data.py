# sourcery skip: no-wildcard-imports
from pathlib import Path
from typing import Callable, Generator

import pytest
from pytest_mock import MockerFixture

from sfkit.protocol import register_data
from tests.helper_functions_and_constants import *


def test_register_data(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.authenticate_user")
    mocker.patch("sfkit.protocol.register_data.get_username", return_value="user@example.com")
    mocker.patch("sfkit.protocol.register_data.update_firestore")
    mocker.patch("sfkit.protocol.register_data.validate_sfgwas", return_value=("hi", "hello"))
    mocker.patch("sfkit.protocol.register_data.validate_mpcgwas")
    mocker.patch("sfkit.protocol.register_data.validate_pca")
    mocker.patch("sfkit.protocol.register_data.encrypt_mpcgwas")
    mocker.patch("sfkit.protocol.register_data.checksumdir.dirhash", return_value="sha1hash")
    mocker.patch("sfkit.protocol.register_data.open", mocker.mock_open())

    local_mock_doc_ref_dict = {
        "status": {"user@example.com": "start"},
        "participants": ["user@example.com"],
        "study_type": "SF-GWAS",
        "description": "",
    }

    mocker.patch("sfkit.protocol.register_data.get_doc_ref_dict", return_value=local_mock_doc_ref_dict)

    # Test SF-GWAS
    register_data.register_data("geno_binary_file_prefix", "data_path")

    # Test MPC-GWAS
    local_mock_doc_ref_dict["study_type"] = "MPC-GWAS"
    register_data.register_data("geno_binary_file_prefix", "data_path")

    # Test PCA
    local_mock_doc_ref_dict["study_type"] = "PCA"
    register_data.register_data("geno_binary_file_prefix", "data_path")

    # Test unknown study type
    local_mock_doc_ref_dict["study_type"] = "UNKNOWN-STUDY-TYPE"
    with pytest.raises(ValueError):
        register_data.register_data("geno_binary_file_prefix", "data_path")

    local_mock_doc_ref_dict["study_type"] = "SF-GWAS"
    local_mock_doc_ref_dict["description"] = "usingblocks-"
    mocker.patch("sfkit.protocol.register_data.get_doc_ref_dict", return_value=local_mock_doc_ref_dict)
    register_data.register_data("geno_binary_file_prefix", "data_path")

    local_mock_doc_ref_dict["status"]["user@example.com"] = "validated"
    mocker.patch("sfkit.protocol.register_data.get_doc_ref_dict", return_value=local_mock_doc_ref_dict)
    register_data.register_data("geno_binary_file_prefix", "data_path")


def test_encrypt_mpcgwas(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.update_firestore")
    mocker.patch("sfkit.protocol.register_data.encrypt_data")
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")

    register_data.encrypt_mpcgwas("1", "PCA")
    register_data.encrypt_mpcgwas("1", "MPC-GWAS")

    mocker.patch("sfkit.protocol.register_data.encrypt_data", side_effect=Exception("error"))
    register_data.encrypt_mpcgwas("1", "MPC-GWAS")


def test_validate_sfgwas(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.validate_geno_binary_file_prefix")
    mocker.patch("sfkit.protocol.register_data.validate_data_path", lambda x: x)
    mocker.patch("sfkit.protocol.register_data.using_demo")
    mocker.patch("sfkit.protocol.register_data.validate_sfgwas_data")
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")
    mocker.patch("sfkit.protocol.register_data.num_rows")

    register_data.validate_sfgwas(mock_doc_ref_dict, "a@a.com", "data_path", "geno_binary_file_prefix")
    register_data.validate_sfgwas(mock_doc_ref_dict, "a@a.com", "demo", "geno_binary_file_prefix")

    mock_doc_ref_dict_copy = copy.deepcopy(mock_doc_ref_dict)
    mock_doc_ref_dict_copy["personal_parameters"]["a@a.com"]["NUM_INDS"]["value"] = 5
    register_data.validate_sfgwas(mock_doc_ref_dict_copy, "a@a.com", "data_path", "geno_binary_file_prefix")


def test_validate_mpcgwas(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.validate_data_path", lambda x: x)
    mocker.patch("sfkit.protocol.register_data.using_demo")
    mocker.patch("sfkit.protocol.register_data.validate_mpcgwas_data", return_value=(1, 1))
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")
    mocker.patch("sfkit.protocol.register_data.website_send_file")
    mocker.patch("sfkit.protocol.register_data.open")

    register_data.validate_mpcgwas(mock_doc_ref_dict, "a@a.com", "data_path", "1")
    register_data.validate_mpcgwas(mock_doc_ref_dict, "a@a.com", "demo", "0")


def test_validate_pca(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.validate_data_path", lambda x: x)
    mocker.patch("sfkit.protocol.register_data.using_demo")
    mocker.patch("sfkit.protocol.register_data.num_rows")
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")
    mocker.patch("sfkit.protocol.register_data.num_cols")

    register_data.validate_pca(mock_doc_ref_dict, "a@a.com", "data_path")
    register_data.validate_pca(mock_doc_ref_dict, "a@a.com", "demo")


def test_validate_geno_binary_file_prefix(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    # sourcery skip: remove-redundant-fstring
    mocker.patch("sfkit.protocol.register_data.input", return_value="demo")
    mocker.patch("sfkit.protocol.register_data.os.path.isabs", return_value=False)

    assert register_data.validate_geno_binary_file_prefix("") == "demo"

    mocker.patch("sfkit.protocol.register_data.input", return_value="")
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        register_data.validate_geno_binary_file_prefix("geno_binary_file_prefix")

    mocker.patch("sfkit.protocol.register_data.constants.IS_DOCKER", True)
    mocker.patch("sfkit.protocol.register_data.os.path.isabs", return_value=True)
    mocker.patch("os.path.exists", return_value=True)
    assert register_data.validate_geno_binary_file_prefix("") == f"/app/data/geno/ch%d"


def test_validate_data_path(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.input", return_value="demo")
    mocker.patch("sfkit.protocol.register_data.os.path.isabs", return_value=False)

    assert register_data.validate_data_path("") == "demo"

    mocker.patch("sfkit.protocol.register_data.input", return_value="")
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        register_data.validate_data_path("data_path")

    mocker.patch("sfkit.protocol.register_data.constants.IS_DOCKER", True)
    mocker.patch("sfkit.protocol.register_data.os.path.isabs", return_value=True)
    mocker.patch("os.path.exists", return_value=True)
    assert register_data.validate_data_path("") == "/app/data"


def test_validate_sfgwas_data(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")
    mocker.patch("sfkit.protocol.register_data.os.path.isfile", return_value=True)
    mocker.patch("sfkit.protocol.register_data.num_rows", return_value=1)
    mocker.patch("sfkit.protocol.register_data.find_duplicate_line")

    assert register_data.validate_sfgwas_data("geno_binary_file_prefix%d", "data_path") == 1


def test_validate_mpcgwas_data(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.num_rows", return_value=1)
    mocker.patch("sfkit.protocol.register_data.num_cols", return_value=1)
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")
    mocker.patch("sfkit.protocol.register_data.find_duplicate_line")

    assert register_data.validate_mpcgwas_data("data_path") == (1, 1)


def test_num_rows(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.open", return_value=[1, 2, 3])

    assert register_data.num_rows("data_path") == 3


def test_num_cols(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    # mock open to something that I can call readline on
    mocker.patch("sfkit.protocol.register_data.open", return_value=MockFile())

    assert register_data.num_cols("data_path") == 3


def test_using_demo(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.protocol.register_data.update_firestore")

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        register_data.using_demo()


def test_find_duplicate_line(tmpdir: Path) -> None:
    # sourcery skip: extract-duplicate-method
    tmpdir = Path(str(tmpdir))

    # Create a file with some content, including a duplicate line
    file_with_duplicates = tmpdir / "file_with_duplicates.txt"
    with file_with_duplicates.open("w") as f:
        f.write("Line 1\n")
        f.write("Line 2\n")
        f.write("Line 2\n")
        f.write("Line 3\n")
        f.write("Line 4\n")

    # Test with a file containing a duplicate line
    duplicate_line = register_data.find_duplicate_line(str(file_with_duplicates))
    assert duplicate_line == "Line 2", f"Expected 'Line 2', but got {duplicate_line}"

    # Create a file with no duplicate lines
    file_without_duplicates = tmpdir / "file_without_duplicates.txt"
    with file_without_duplicates.open("w") as f:
        f.write("Line 1\n")
        f.write("Line 2\n")
        f.write("Line 3\n")
        f.write("Line 4\n")

    # Test with a file containing no duplicate lines
    no_duplicate_line = register_data.find_duplicate_line(str(file_without_duplicates))
    assert no_duplicate_line is None, f"Expected None, but got {no_duplicate_line}"


class MockFile:
    def readline(self):
        return "1 2 3"
