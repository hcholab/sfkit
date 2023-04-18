# # sourcery skip: no-wildcard-imports, require-parameter-annotation, require-return-annotation

# import pytest
# from sfkit.protocol import run_protocol
# from tests.helper_functions_and_constants import *


# def test_run_protocol(mocker):
#     # mock authenticate_user
#     mocker.patch("sfkit.protocol.run_protocol.authenticate_user")
#     # mock get_doc_ref_dict
#     mocker.patch("sfkit.protocol.run_protocol.get_doc_ref_dict", return_value=mock_doc_ref_dict)
#     mocker.patch("sfkit.protocol.run_protocol.get_username", return_value="a@a.com")
#     # mock update_firestore
#     mocker.patch("sfkit.protocol.run_protocol.update_firestore")
#     # mock time.sleep
#     mocker.patch("sfkit.protocol.run_protocol.time.sleep")
#     # mock create_cp0
#     mocker.patch("sfkit.protocol.run_protocol.create_cp0")
#     # mock run_gwas_protocol
#     mocker.patch("sfkit.protocol.run_protocol.run_gwas_protocol")
#     # mock run_sfgwas_protocol
#     mocker.patch("sfkit.protocol.run_protocol.run_sfgwas_protocol")
#     # mock run_pca protocol
#     mocker.patch("sfkit.protocol.run_protocol.run_pca_protocol")
#     # mock other_participant_not_ready
#     mocker.patch("sfkit.protocol.run_protocol.other_participant_not_ready", side_effect=[True] + [False] * 10)

#     # expect ValueError
#     with pytest.raises(ValueError):
#         run_protocol.run_protocol(phase="5")

#     run_protocol.run_protocol()

#     mock_doc_ref_dict_copy = copy.deepcopy(mock_doc_ref_dict)
#     mock_doc_ref_dict_copy["status"]["a@a.com"] = "validated data"
#     mocker.patch("sfkit.protocol.run_protocol.get_doc_ref_dict", return_value=mock_doc_ref_dict_copy)
#     run_protocol.run_protocol()

#     mock_doc_ref_dict_copy["status"]["b@b.com"] = "validated data"
#     mock_doc_ref_dict_copy["study_type"] = "MPC-GWAS"
#     mocker.patch("sfkit.protocol.run_protocol.get_username", return_value="b@b.com")
#     run_protocol.run_protocol(phase="1")

#     mock_doc_ref_dict_copy["study_type"] = "PCA"
#     run_protocol.run_protocol()

#     mock_doc_ref_dict_copy["study_type"] = "garbage"
#     with pytest.raises(ValueError):
#         run_protocol.run_protocol()


# def test_other_participant_not_ready(mocker):
#     assert run_protocol.other_participant_not_ready([]) == False
