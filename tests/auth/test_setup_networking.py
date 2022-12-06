# sourcery skip: require-parameter-annotation, require-return-annotation
import pytest
from sfkit.auth import setup_networking


def test_setup_networking(mocker):
    mocker.patch("sfkit.auth.setup_networking.get_doc_ref_dict", return_value={"participants": ["a@a.com", "b@b.com"]})
    mocker.patch("sfkit.auth.setup_networking.update_firestore")
    mocker.patch("sfkit.auth.setup_networking.get_username", return_value="a@a.com")
    mocker.patch("sfkit.auth.setup_networking.authenticate_user")
    mocker.patch("sfkit.auth.setup_networking.input", return_value="8000")
    mocker.patch("sfkit.auth.setup_networking.socket.gethostbyname", return_value="170.0.0.1")
    mocker.patch("sfkit.auth.setup_networking.socket.gethostname")
    mocker.patch("sfkit.auth.setup_networking.get")

    setup_networking.setup_networking("")

    setup_networking.setup_networking("8000")

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        setup_networking.setup_networking("1,2,3")
