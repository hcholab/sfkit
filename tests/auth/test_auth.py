# # sourcery skip: avoid-single-character-names-variables, require-parameter-annotation, require-return-annotation

# import io
# import pytest
# from sfkit.auth import auth


# def test_auth(mocker):
#     mocker.patch("sfkit.auth.auth.open", mock_open)
#     mocker.patch("sfkit.auth.auth.input", return_value="")
#     mocker.patch("sfkit.auth.auth.get_doc_ref_dict")
#     mocker.patch("sfkit.auth.auth.condition_or_fail")
#     mocker.patch("sfkit.auth.auth.os.makedirs")
#     mocker.patch("sfkit.auth.auth.os.remove")

#     auth.auth()

#     mocker.patch("sfkit.auth.auth.get_doc_ref_dict", side_effect=Exception)
#     with pytest.raises(SystemExit) as pytest_wrapped_e:
#         auth.auth()

#     mocker.patch("sfkit.auth.auth.open", side_effect=FileNotFoundError)
#     with pytest.raises(SystemExit) as pytest_wrapped_e:
#         auth.auth()

#     mocker.patch("sfkit.auth.auth.open", mock_broken_open)
#     with pytest.raises(SystemExit) as pytest_wrapped_e:
#         auth.auth()


# def mock_open(path, mode):
#     return io.StringIO("")


# def mock_broken_open(path, mode):
#     if path == "auth_key.txt":
#         raise FileNotFoundError
#     return io.StringIO("")
