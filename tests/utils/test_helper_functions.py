import os
from pathlib import Path
import shutil
from typing import Callable, Generator

import numpy as np
import pytest
from google.cloud import storage
from pytest_mock import MockerFixture

from sfkit.utils import helper_functions


def test_authenticate_user(mocker: Callable[..., Generator[MockerFixture, None, None]]) -> None:
    # mock os.path.exists
    mocker.patch("sfkit.utils.helper_functions.os.path.exists")
    helper_functions.authenticate_user()

    mocker.patch("sfkit.utils.helper_functions.os.path.exists", return_value=False)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        helper_functions.authenticate_user()


def test_run_command(mocker: Callable[..., Generator[MockerFixture, None, None]]) -> None:
    mocker.patch("sfkit.utils.helper_functions.condition_or_fail")
    helper_functions.run_command_shell_equals_true("true")
    helper_functions.run_command_shell_equals_true('echo "Hello, World!"')

    # failure
    helper_functions.run_command_shell_equals_true("asdf")


def test_condition_or_fail(mocker: Callable[..., Generator[MockerFixture, None, None]]) -> None:
    # mock update_firestore
    mocker.patch("sfkit.utils.helper_functions.update_firestore")

    helper_functions.condition_or_fail(True)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        helper_functions.condition_or_fail(False)


def test_postprocess_assoc(tmpdir: Path, mocker: Callable[..., Generator[MockerFixture, None, None]]):
    tmpdir = Path(str(tmpdir))

    mocker.patch(
        "numpy.loadtxt",
        side_effect=[
            np.array([True, False, True]),  # gkeep1
            np.array([1.0, 2.0]),  # assoc
        ],
    )
    mocker.patch("numpy.log10", return_value=np.array([1.0, 2.0]))
    mocker.patch("scipy.stats.chi2.sf", return_value=np.array([1.0, 1.0]))

    # Create test files
    pos_file = tmpdir / "pos.txt"
    pos_file.write_text("1\t100\n2\t200\n3\t300\n")

    gkeep1_file = tmpdir / "gkeep1.txt"
    gkeep1_file.write_text("True\nFalse\nTrue\n")

    new_assoc_file = tmpdir / "new_assoc.txt"

    # Call the postprocess_assoc function
    helper_functions.postprocess_assoc(str(new_assoc_file), "assoc_file", str(pos_file), str(gkeep1_file), "", 100, 2)

    # Assert the expected behavior
    np.loadtxt.assert_any_call("assoc_file")
    np.loadtxt.assert_any_call(str(gkeep1_file), dtype=bool)

    # Check the content of the output file
    with open(new_assoc_file, "r") as f:
        content = f.read()

    expected_content = "#CHROM\tPOS\tR\tLOG10P\n" "1\t100\t1.0\t1.0\n" "3\t300\t2.0\t2.0\n"

    assert content == expected_content

    mocker.patch(
        "numpy.loadtxt",
        side_effect=[
            np.array([True, False, True]),  # gkeep1
            np.array([True, True]),  # gkeep2
            np.array([1.0, 2.0]),  # assoc
        ],
    )
    helper_functions.postprocess_assoc(
        str(new_assoc_file), "assoc_file", str(pos_file), str(gkeep1_file), str(tmpdir / "gkeep2.txt"), 100, 2
    )


def test_plot_assoc(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    # Mock the objects and functions
    mocker.patch("pandas.read_table")
    mocker.patch("matplotlib.pyplot.figure")
    mocker.patch("matplotlib.pyplot.savefig")
    mocker.patch("sfkit.utils.helper_functions.manhattanplot")

    # Call the plot_assoc function
    helper_functions.plot_assoc("plot_file", "new_assoc_file")


def test_copy_results_to_cloud_storage(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("os.makedirs")
    mocker.patch("shutil.copyfile")
    mocker.patch("os.listdir", return_value=["Qpc.txt"])

    mock_storage_client = mocker.patch("google.cloud.storage.Client")
    mock_bucket = mocker.MagicMock(spec=storage.Bucket)
    mock_blob = mocker.MagicMock(spec=storage.Blob)

    mock_storage_client.return_value = mock_storage_client
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    # Call the copy_results_to_cloud_storage function
    helper_functions.copy_results_to_cloud_storage("1", "bucket_name/prefix", "sfgwas_output_directory")

    # Assert the expected behavior
    os.makedirs.assert_called_once_with("sfgwas_output_directory", exist_ok=True)
    shutil.copyfile.assert_called_once_with("sfgwas/cache/party1/Qpc.txt", "sfgwas_output_directory/Qpc.txt")
    os.listdir.assert_called_once_with("sfgwas_output_directory")
    mock_storage_client.bucket.assert_called_once_with("bucket_name")
    mock_bucket.blob.assert_called_once_with("prefix/out/party1/Qpc.txt")
    mock_blob.upload_from_filename.assert_called_once_with("sfgwas_output_directory/Qpc.txt")

    # failure case
    mock_storage_client = mocker.patch("google.cloud.storage.Client", side_effect=Exception("test"))
    helper_functions.copy_results_to_cloud_storage("1", "bucket_name/prefix", "output_directory")


def test_copy_to_out_folder(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    # sourcery skip: extract-duplicate-method
    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.makedirs")
    mocker.patch("os.path.isfile", return_value=True)
    mocker.patch("shutil.copy2")
    mocker.patch("os.path.isdir", return_value=True)
    mocker.patch("shutil.copytree")
    mocker.patch("shutil.rmtree")

    helper_functions.copy_to_out_folder(["file1"])

    mocker.patch("os.path.isfile", return_value=False)
    helper_functions.copy_to_out_folder(["file1"])

    mocker.patch("os.path.exists", side_effect=[True, True, False])
    helper_functions.copy_to_out_folder(["file1"])

    mocker.patch("os.path.exists", return_value=True)
    mocker.patch("os.path.isdir", return_value=False)
    helper_functions.copy_to_out_folder(["file1"])

    mocker.patch("os.path.exists", return_value=False)
    helper_functions.copy_to_out_folder(["file1"])
