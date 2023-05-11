# sourcery skip: no-wildcard-imports
from typing import Callable, Generator
from pytest_mock import MockerFixture
from sfkit.utils import gwas_protocol
from tests.helper_functions_and_constants import *

undo_mock_changes()


def test_run_gwas_protocol(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.install_gwas_dependencies")
    mocker.patch("sfkit.utils.gwas_protocol.install_gwas_repo")
    mocker.patch("sfkit.utils.gwas_protocol.install_ntl_library")
    mocker.patch("sfkit.utils.gwas_protocol.compile_gwas_code")
    mocker.patch("sfkit.utils.gwas_protocol.update_parameters")
    # mocker.patch("sfkit.utils.gwas_protocol.connect_to_other_vms")
    mocker.patch("sfkit.utils.gwas_protocol.prepare_data")
    mocker.patch("sfkit.utils.gwas_protocol.copy_data_to_gwas_repo")
    mocker.patch("sfkit.utils.gwas_protocol.sync_with_other_vms")
    mocker.patch("sfkit.utils.gwas_protocol.start_datasharing")
    mocker.patch("sfkit.utils.gwas_protocol.start_gwas")

    gwas_protocol.run_gwas_protocol("1")
    gwas_protocol.run_gwas_protocol("1", demo=True)

    mocker.patch("sfkit.utils.gwas_protocol.constants.IS_DOCKER", True)
    gwas_protocol.run_gwas_protocol("1")


def test_install_gwas_dependencies(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.run_command")
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")

    gwas_protocol.install_gwas_dependencies()


def test_install_gwas_repo(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.run_command")
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")

    gwas_protocol.install_gwas_repo()


def test_install_ntl_library(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.run_command")
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")

    gwas_protocol.install_ntl_library()


def test_compile_gwas_code(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.run_command")
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")

    gwas_protocol.compile_gwas_code()


def test_update_parameters(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")
    mocker.patch("sfkit.utils.gwas_protocol.fileinput.input", mock_fileinput_input)
    mocker.patch("sfkit.utils.gwas_protocol.get_doc_ref_dict", return_value=mock_doc_ref_dict)

    gwas_protocol.update_parameters("1")


# def test_connect_to_other_vms(mocker):
#     # mock subprocess.run
#     mocker.patch("sfkit.utils.gwas_protocol.subprocess.run", return_value=Mock_Subprocess(0))
#     # mock update_firestore
#     mocker.patch("sfkit.utils.gwas_protocol.update_firestore")
#     # mock time.sleep
#     mocker.patch("sfkit.utils.gwas_protocol.time.sleep", mock_sleep)

#     gwas_protocol.connect_to_other_vms(mock_doc_ref_dict, "1")

#     mocker.patch("sfkit.utils.gwas_protocol.subprocess.run", return_value=Mock_Subprocess(1))
#     with pytest.raises(SystemExit) as pytest_wrapped_e:
#         gwas_protocol.connect_to_other_vms(mock_doc_ref_dict, "1")

#     mocker.patch("sfkit.utils.gwas_protocol.subprocess.run", mock_subprocess_run)
#     mock_doc_ref_dict["personal_parameters"]["a@a.com"]["IP_ADDRESS"]["value"] = "bad"
#     gwas_protocol.connect_to_other_vms(mock_doc_ref_dict, "2")


def test_encrypt_or_prepare_data(mocker):
    mocker.patch("google.cloud.storage.Client")
    mocker.patch("sfkit.utils.gwas_protocol.get_doc_ref_dict", return_value=mock_doc_ref_dict)

    gwas_protocol.prepare_data("data_path", "0")
    gwas_protocol.prepare_data("data_path", "1")


def test_copy_data_to_gwas_repo(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.run_command")
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")

    gwas_protocol.copy_data_to_gwas_repo("data_path", "0")
    gwas_protocol.copy_data_to_gwas_repo("data_path", "1")


def test_sync_with_other_vms(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch(
        "sfkit.utils.gwas_protocol.get_doc_ref_dict", side_effect=[mock_doc_ref_dict, mock_doc_ref_dict_syncing_up]
    )
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")
    mocker.patch("sfkit.utils.gwas_protocol.time.sleep")

    gwas_protocol.sync_with_other_vms("0")


def test_start_datasharing(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.gwas_protocol.run_command")
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")
    mocker.patch("sfkit.utils.gwas_protocol.time.sleep")

    gwas_protocol.start_datasharing("0", True)
    gwas_protocol.start_datasharing("0", False)
    gwas_protocol.start_datasharing("1", False)


def test_start_gwas(mocker):
    mocker.patch("sfkit.utils.gwas_protocol.run_command")
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")
    mocker.patch("sfkit.utils.gwas_protocol.time.sleep")
    mocker.patch("sfkit.utils.gwas_protocol.open")
    mocker.patch("sfkit.utils.gwas_protocol.process_output_files")

    gwas_protocol.start_gwas("0", True)
    gwas_protocol.start_gwas("0", False)
    gwas_protocol.start_gwas("1", False)


def test_process_output_files(mocker):
    mocker.patch("sfkit.utils.gwas_protocol.update_firestore")
    mocker.patch("sfkit.utils.gwas_protocol.get_doc_ref_dict", return_value=mock_doc_ref_dict)
    mocker.patch("sfkit.utils.gwas_protocol.postprocess_assoc")
    mocker.patch("sfkit.utils.gwas_protocol.plot_assoc")
    mocker.patch("sfkit.utils.gwas_protocol.copy_results_to_cloud_storage")
    mocker.patch("sfkit.utils.gwas_protocol.website_send_file")
    mocker.patch("sfkit.utils.gwas_protocol.open")

    gwas_protocol.process_output_files("0", True)
    gwas_protocol.process_output_files("0", False)
    gwas_protocol.process_output_files("1", False)
