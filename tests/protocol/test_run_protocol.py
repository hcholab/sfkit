# sourcery skip: no-wildcard-imports
import pytest
from helper_functions_and_constants import *

from sfkit.protocol import run_protocol


def test_run_protocol(mocker):
    mocker.patch("sfkit.protocol.run_protocol.authenticate_user")
    mocker.patch("sfkit.protocol.run_protocol.get_doc_ref_dict", return_value=mock_doc_ref_dict)
    mocker.patch("sfkit.protocol.run_protocol.get_username", return_value="a@a.com")
    mocker.patch("sfkit.protocol.run_protocol.update_firestore")
    mocker.patch("sfkit.protocol.run_protocol.time.sleep")
    mocker.patch("sfkit.protocol.run_protocol.create_cp0")
    mocker.patch("sfkit.protocol.run_protocol.run_gwas_protocol")
    mocker.patch("sfkit.protocol.run_protocol.run_sfgwas_protocol")
    mocker.patch("sfkit.protocol.run_protocol.run_pca_protocol")
    mocker.patch("sfkit.protocol.run_protocol.other_participant_not_ready", side_effect=[True] + [False] * 10)

    with pytest.raises(ValueError):
        run_protocol.run_protocol(phase="5")

    with pytest.raises(SystemExit):
        run_protocol.run_protocol(send_results="Yes", results_path="path/to/results")

    mock_doc_ref_dict_copy = copy.deepcopy(mock_doc_ref_dict)
    mock_doc_ref_dict_copy["status"]["a@a.com"] = "validated data"
    mocker.patch("sfkit.protocol.run_protocol.get_doc_ref_dict", return_value=mock_doc_ref_dict_copy)
    run_protocol.run_protocol()

    mock_doc_ref_dict_copy["status"]["b@b.com"] = "validated data"
    mock_doc_ref_dict_copy["study_type"] = "MPC-GWAS"
    mocker.patch("sfkit.protocol.run_protocol.get_username", return_value="b@b.com")
    run_protocol.run_protocol(phase="1")

    mock_doc_ref_dict_copy["study_type"] = "PCA"
    run_protocol.run_protocol()

    mock_doc_ref_dict_copy["study_type"] = "garbage"
    mock_doc_ref_dict_copy["demo"] = True
    with pytest.raises(ValueError):
        run_protocol.run_protocol()


def test_other_participant_not_ready(mocker):
    assert run_protocol.other_participant_not_ready([]) == False
