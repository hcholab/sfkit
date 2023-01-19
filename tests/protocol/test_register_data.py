# sourcery skip: docstrings-for-classes, no-wildcard-imports, require-parameter-annotation, require-return-annotation
from io import StringIO
import pytest
from sfkit.protocol import register_data
from tests.helper_functions_and_constants import *


# def test_register_data(mocker):
#     # mock authenticate_user
#     mocker.patch("sfkit.protocol.register_data.authenticate_user")
#     mocker.patch("sfkit.protocol.register_data.get_username", return_value="a@a.com")
#     # mock get_doc_ref_dict
#     mocker.patch("sfkit.protocol.register_data.get_doc_ref_dict", return_value=mock_doc_ref_dict)
#     # mock validate_geno_binary_file_prefix
#     mocker.patch(
#         "sfkit.protocol.register_data.validate_geno_binary_file_prefix", return_value="geno_binary_file_prefix"
#     )
#     # mock validate_data_path
#     mocker.patch("sfkit.protocol.register_data.validate_data_path", lambda x: x)
#     # mock using_demo
#     mocker.patch("sfkit.protocol.register_data.using_demo", return_value=True)
#     # mock validate_sfgwas_data
#     mocker.patch("sfkit.protocol.register_data.validate_sfgwas_data", return_value=1)
#     # mock condition_or_fail
#     mocker.patch("sfkit.protocol.register_data.condition_or_fail")
#     # mock num_rows
#     mocker.patch("sfkit.protocol.register_data.num_rows", return_value=1)
#     # mock validate_mpcgwas_data
#     mocker.patch("sfkit.protocol.register_data.validate_mpcgwas_data", return_value=1)
#     # mock num_cols
#     mocker.patch("sfkit.protocol.register_data.num_cols", return_value=1)
#     # mock update_firestore
#     mocker.patch("sfkit.protocol.register_data.update_firestore")
#     # mock checksum.dirhash
#     mocker.patch("sfkit.protocol.register_data.checksumdir.dirhash", return_value="hash")
#     # mock open
#     mocker.patch("sfkit.protocol.register_data.open")

#     register_data.register_data("geno_binary_file_prefix", "data_path")
#     register_data.register_data("demo", "demo")

#     mocker.patch("sfkit.protocol.register_data.get_doc_ref_dict", return_value=mock_doc_ref_dict_mpcgwas)
#     register_data.register_data("geno_binary_file_prefix", "data_path")
#     register_data.register_data("demo", "demo")

#     mocker.patch("sfkit.protocol.register_data.get_doc_ref_dict", return_value=mock_doc_ref_dict_pca)
#     register_data.register_data("geno_binary_file_prefix", "data_path")
#     register_data.register_data("demo", "demo")

#     mock_doc_ref_dict_no_study_type = copy.deepcopy(mock_doc_ref_dict)
#     mock_doc_ref_dict_no_study_type["study_type"] = ""
#     mocker.patch("sfkit.protocol.register_data.get_doc_ref_dict", return_value=mock_doc_ref_dict_no_study_type)
#     # expect ValueError
#     with pytest.raises(ValueError):
#         register_data.register_data("geno_binary_file_prefix", "data_path")


def test_validate_geno_binary_file_prefix(mocker):
    # mock input
    mocker.patch("sfkit.protocol.register_data.input", return_value="demo")
    # mock os.path.isabs to false
    mocker.patch("sfkit.protocol.register_data.os.path.isabs", return_value=False)

    assert register_data.validate_geno_binary_file_prefix("") == "demo"

    mocker.patch("sfkit.protocol.register_data.input", return_value="")
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        register_data.validate_geno_binary_file_prefix("geno_binary_file_prefix")


def test_validate_data_path(mocker):
    # mock input
    mocker.patch("sfkit.protocol.register_data.input", return_value="demo")
    # mock os.path.isabs to false
    mocker.patch("sfkit.protocol.register_data.os.path.isabs", return_value=False)

    assert register_data.validate_data_path("") == "demo"

    mocker.patch("sfkit.protocol.register_data.input", return_value="")
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        register_data.validate_data_path("data_path")


def test_validate_sfgwas_data(mocker):
    # mock condition_or_fail
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")
    # mock os.path.isfile
    mocker.patch("sfkit.protocol.register_data.os.path.isfile", return_value=True)
    # mock num_rows
    mocker.patch("sfkit.protocol.register_data.num_rows", return_value=1)

    assert register_data.validate_sfgwas_data("geno_binary_file_prefix%d", "data_path") == 1


def test_validate_mpcgwas_data(mocker):
    # mock num_rows
    mocker.patch("sfkit.protocol.register_data.num_rows", return_value=1)
    # mock condition_or_fail
    mocker.patch("sfkit.protocol.register_data.condition_or_fail")

    assert register_data.validate_mpcgwas_data("data_path") == 1


def test_num_rows(mocker):
    # mock open
    mocker.patch("sfkit.protocol.register_data.open", return_value=[1, 2, 3])

    assert register_data.num_rows("data_path") == 3


def test_num_cols(mocker):
    # mock open to something that I can call readline on
    mocker.patch("sfkit.protocol.register_data.open", return_value=MockFile())

    assert register_data.num_cols("data_path") == 3


def test_using_demo(mocker):
    # mock update_firestore
    mocker.patch("sfkit.protocol.register_data.update_firestore")

    assert register_data.using_demo() == True


class MockFile:
    def readline(self):
        return "1 2 3"
