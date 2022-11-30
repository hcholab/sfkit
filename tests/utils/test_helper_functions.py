# sourcery skip: require-parameter-annotation
import pytest
from sfkit.utils import helper_functions
from tests.helper_functions_and_constants import Mock_Subprocess


def test_authenticate_user(mocker) -> None:
    # mock os.path.exists
    mocker.patch("sfkit.utils.helper_functions.os.path.exists")
    helper_functions.authenticate_user()

    mocker.patch("sfkit.utils.helper_functions.os.path.exists", return_value=False)
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        helper_functions.authenticate_user()


def test_run_command(mocker) -> None:
    # mock subprocess.run
    mocker.patch("sfkit.utils.helper_functions.subprocess.run", return_value=Mock_Subprocess(0))
    helper_functions.run_command("")

    mocker.patch("sfkit.utils.helper_functions.subprocess.run", return_value=Mock_Subprocess(1))
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        helper_functions.run_command("bad_command")


def test_condition_or_fail(mocker) -> None:
    # mock update_firestore
    mocker.patch("sfkit.utils.helper_functions.update_firestore")

    helper_functions.condition_or_fail(True)

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        helper_functions.condition_or_fail(False)
