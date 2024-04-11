from io import BytesIO
import math
import select
import subprocess
from pathlib import Path
from typing import Callable, Generator
from unittest.mock import MagicMock, Mock, call, mock_open, patch

import matplotlib.pyplot as plt
import numpy as np
import pytest
from pytest_mock import MockerFixture
import requests

from sfkit.utils import constants, sfgwas_helper_functions


def test_get_file_paths(tmp_path: Path):
    # Create a temporary data path file with sample content
    data_path_file = tmp_path / "data_path.txt"
    data_path_file.write_text("geno\npath/to/data\n")

    # Set the SFKIT_DIR constant to the temporary directory
    constants.SFKIT_DIR = str(tmp_path)

    # Call the function and check the return values
    geno_file_prefix, data_path = sfgwas_helper_functions.get_file_paths()
    assert geno_file_prefix == "geno"
    assert data_path == "path/to/data"


def test_use_existing_config(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.sfgwas_helper_functions.get_file_paths", return_value=("prefix", "/data/path"))
    mocker.patch("sfkit.utils.sfgwas_helper_functions.move", return_value=None)

    doc_ref_dict = {"description": "usingblocks-config"}
    sfgwas_helper_functions.use_existing_config("1", doc_ref_dict)

    sfgwas_helper_functions.use_existing_config("0", doc_ref_dict)


def test_move(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("shutil.rmtree", return_value=None)
    mocker.patch("shutil.move", return_value=None)

    source = "source"
    destination = "destination"
    sfgwas_helper_functions.move(source, destination)


def test_run_sfprotocol_with_task_updates(mocker: Callable[..., Generator[MockerFixture, None, None]]) -> None:
    mocker.patch("sfkit.utils.sfgwas_helper_functions.condition_or_fail")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.update_firestore")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.check_for_failure")

    sfgwas_helper_functions.run_sfprotocol_with_task_updates("true", "SF-GWAS", "1")
    sfgwas_helper_functions.run_sfprotocol_with_task_updates('echo "sfkit: hi"', "PCA", "1")
    sfgwas_helper_functions.run_sfprotocol_with_task_updates(
        'echo "Output collectively decrypted and saved to"', "", "1"
    )

    mocker.patch(
        "sfkit.utils.sfgwas_helper_functions.select.select",
        side_effect=(
            [[BytesIO("Output collectively decrypted and saved to".encode())], [], []],
            [[], [], []],
            [[], [], []],
        ),
    )

    sfgwas_helper_functions.run_sfprotocol_with_task_updates(
        'echo "Output collectively decrypted and saved to"; echo "hi"', "", "1"
    )
    sfgwas_helper_functions.run_sfprotocol_with_task_updates('echo "hi"', "", "1")


def test_check_for_failure(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.sfgwas_helper_functions.condition_or_fail")

    command = "my_command"
    protocol = "my_protocol"
    process = Mock(spec=subprocess.Popen)
    stream = MagicMock(name="stderr")
    process.stderr = stream
    line = "my error message"

    sfgwas_helper_functions.check_for_failure(command, protocol, process, stream, line)

    sfgwas_helper_functions.check_for_failure(command, protocol, process, stream, "warning: my warning message")


def test_post_process_results(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    # Mock external functions
    mocker.patch(
        "sfkit.utils.sfgwas_helper_functions.get_doc_ref_dict",
        return_value={
            "participants": {1: "user_id_1", 2: "user_id_2"},
            "personal_parameters": {
                "user_id_1": {"RESULTS_PATH": {"value": "results_path_1"}, "SEND_RESULTS": {"value": "Yes"}},
                "user_id_2": {"RESULTS_PATH": {"value": "results_path_2"}, "SEND_RESULTS": {"value": "Yes"}},
            },
        },
    )
    mocker.patch("sfkit.utils.sfgwas_helper_functions.make_new_assoc_and_manhattan_plot")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.make_pca_plot")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.copy_results_to_cloud_storage")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.website_send_file")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.update_firestore")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.open")

    sfgwas_helper_functions.post_process_results("1", True, "SF-GWAS")
    sfgwas_helper_functions.post_process_results("1", True, "PCA")

    mocker.patch(
        "sfkit.utils.sfgwas_helper_functions.get_doc_ref_dict",
        return_value={
            "participants": {1: "user_id_1", 2: "user_id_2"},
            "personal_parameters": {
                "user_id_1": {"RESULTS_PATH": {"value": ""}, "SEND_RESULTS": {"value": "Yes"}},
                "user_id_2": {"RESULTS_PATH": {"value": ""}, "SEND_RESULTS": {"value": "Yes"}},
            },
        },
    )
    sfgwas_helper_functions.post_process_results("1", True, "Other")


def test_make_pca_plot(tmp_path: Path, mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("numpy.loadtxt")
    mocker.patch("matplotlib.pyplot.scatter")
    mocker.patch("matplotlib.pyplot.xlabel")
    mocker.patch("matplotlib.pyplot.ylabel")
    mocker.patch("matplotlib.pyplot.savefig")

    # Call the function
    sfgwas_helper_functions.make_pca_plot("1")


def test_make_new_assoc_and_manhattan_plot(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.utils.sfgwas_helper_functions.postprocess_assoc")
    mocker.patch("sfkit.utils.sfgwas_helper_functions.plot_assoc")

    # Set up test data and call the function under test
    doc_ref_dict = {
        "personal_parameters": {
            "user1": {"NUM_INDS": {"value": "100"}},
            "user2": {"NUM_INDS": {"value": "200"}},
        },
        "parameters": {"num_covs": {"value": "3"}},
        "participants": ["user1", "user2"],
    }
    sfgwas_helper_functions.make_new_assoc_and_manhattan_plot(doc_ref_dict, demo=False, role="test")
    sfgwas_helper_functions.make_new_assoc_and_manhattan_plot(doc_ref_dict, demo=True, role="test")


def test_to_float_int_or_bool():
    # Test conversion of boolean values
    assert sfgwas_helper_functions.to_float_int_or_bool("true") == True
    assert sfgwas_helper_functions.to_float_int_or_bool("false") == False

    # Test conversion of integer values
    assert sfgwas_helper_functions.to_float_int_or_bool("42") == 42
    assert sfgwas_helper_functions.to_float_int_or_bool("-123") == -123

    # Test conversion of float values
    assert sfgwas_helper_functions.to_float_int_or_bool("3.14") == 3.14
    assert sfgwas_helper_functions.to_float_int_or_bool("-0.5") == -0.5

    # Test conversion of non-numeric/non-boolean values
    assert sfgwas_helper_functions.to_float_int_or_bool("hello") == "hello"
    assert sfgwas_helper_functions.to_float_int_or_bool("") == ""

    # Test conversion of special numeric values
    assert sfgwas_helper_functions.to_float_int_or_bool("inf") == float("inf")
    assert sfgwas_helper_functions.to_float_int_or_bool("-inf") == float("-inf")
