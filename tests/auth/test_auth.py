import io
from typing import Callable, Generator
import pytest
from pytest_mock import MockerFixture
from sfkit.auth import auth


def test_auth(mocker: Callable[..., Generator[MockerFixture, None, None]]):
    mocker.patch("sfkit.auth.auth.open", mock_open)
    mocker.patch("sfkit.auth.auth.input", return_value="")
    mocker.patch("sfkit.auth.auth.get_service_account_headers", return_value="")
    mocker.patch("sfkit.auth.auth.get_study_index", return_value=0)
    mocker.patch(
        "sfkit.auth.auth.get_doc_ref_dict",
        return_value={
            "title": "title",
        },
    )
    mocker.patch(
        "sfkit.auth.auth.get_study_options", return_value={"options": [{"study_id": "123", "title": "Test Study"}]}
    )
    mocker.patch("sfkit.auth.auth.condition_or_fail")
    mocker.patch("sfkit.auth.auth.os.makedirs")
    mocker.patch("sfkit.auth.auth.os.remove")

    auth.auth("")

    mocker.patch("sfkit.auth.auth.get_doc_ref_dict", side_effect=Exception)
    auth.auth("")

    # mocker.patch("sfkit.auth.auth.open", side_effect=FileNotFoundError)
    # with pytest.raises(SystemExit) as pytest_wrapped_e:
    #     auth.auth("")

    # mocker.patch("sfkit.auth.auth.open", mock_broken_open)
    # auth.auth("")


def mock_open(path, mode):
    return io.StringIO("")


def mock_broken_open(path, mode):
    if path == "auth_key.txt":
        raise FileNotFoundError
    return io.StringIO("")
