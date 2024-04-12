# sourcery skip: no-wildcard-imports
from sfkit.utils import sfgwas_protocol
from tests.helper_functions_and_constants import *


def test_run_sfgwas_protocol(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.install_sfgwas")
    mocker.patch("sfkit.utils.sfgwas_protocol.generate_shared_keys")
    mocker.patch("sfkit.utils.sfgwas_protocol.update_config_local")
    mocker.patch("sfkit.utils.sfgwas_protocol.update_config_global")
    mocker.patch("sfkit.utils.sfgwas_protocol.update_config_global_phase")
    mocker.patch("sfkit.utils.sfgwas_protocol.update_sfgwas_go")
    mocker.patch("sfkit.utils.sfgwas_protocol.build_sfgwas")
    mocker.patch("sfkit.utils.sfgwas_protocol.sync_with_other_vms")
    mocker.patch("sfkit.utils.sfgwas_protocol.start_sfgwas")

    sfgwas_protocol.run_sfgwas_protocol("1", demo=True)
    sfgwas_protocol.generate_shared_keys.assert_not_called()

    sfgwas_protocol.run_sfgwas_protocol("1")
    sfgwas_protocol.generate_shared_keys.assert_called_once()

    mocker.patch("sfkit.utils.sfgwas_protocol.constants.IS_DOCKER", True)
    sfgwas_protocol.run_sfgwas_protocol("1")


def test_install_sfgwas(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.os.chdir")
    mocker.patch("sfkit.utils.sfgwas_protocol.run_command")
    mocker.patch("sfkit.utils.sfgwas_protocol.update_firestore")
    mocker.patch("sfkit.utils.sfgwas_protocol.os.path.isdir", return_value=True)
    mocker.patch("sfkit.utils.sfgwas_protocol.condition_or_fail")
    mocker.patch("sfkit.utils.sfgwas_protocol.install_go")

    sfgwas_protocol.install_sfgwas()

    mocker.patch("sfkit.utils.sfgwas_protocol.os.path.isdir", return_value=False)
    sfgwas_protocol.install_sfgwas()


def test_generate_shared_keys(mocker):
    undo_mock_changes()
    mocker.patch("sfkit.utils.sfgwas_protocol.get_doc_ref_dict", mock_get_doc_ref_dict)
    mocker.patch("sfkit.utils.sfgwas_protocol.open")
    mocker.patch("sfkit.utils.sfgwas_protocol.time.sleep", mock_sleep)
    mocker.patch("sfkit.utils.sfgwas_protocol.PrivateKey")
    mocker.patch("sfkit.utils.sfgwas_protocol.PublicKey")
    mocker.patch("sfkit.utils.sfgwas_protocol.condition_or_fail")
    mocker.patch("sfkit.utils.sfgwas_protocol.Box")
    mocker.patch("sfkit.utils.sfgwas_protocol.update_firestore")

    sfgwas_protocol.generate_shared_keys(0)
    undo_mock_changes()
    sfgwas_protocol.generate_shared_keys(1)


def test_update_config_local(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.get_doc_ref_dict", mock_get_doc_ref_dict)
    mocker.patch("sfkit.utils.sfgwas_protocol.tomlkit.parse", mock_toml_load)
    mocker.patch("sfkit.utils.sfgwas_protocol.shutil.copyfile", mock_copyfile)
    mocker.patch("sfkit.utils.sfgwas_protocol.update_data_file_paths")
    mocker.patch("sfkit.utils.sfgwas_protocol.open")
    mocker.patch("sfkit.utils.sfgwas_protocol.tomlkit.dumps")
    mocker.patch("sfkit.utils.sfgwas_protocol.use_existing_config")

    sfgwas_protocol.update_config_local("0", "good path")
    sfgwas_protocol.update_config_local("1", "bad path")

    mock_doc_ref_dict["description"] = "usingblocks-TEST"
    sfgwas_protocol.update_config_local("0", "good path")


def test_update_data_file_paths(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.get_file_paths", return_value=["hi", "hello"])

    sfgwas_protocol.update_data_file_paths(mock_toml_data)


def test_update_config_global(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.get_doc_ref_dict", mock_get_doc_ref_dict)
    mocker.patch("sfkit.utils.sfgwas_protocol.tomlkit.parse", mock_toml_load)
    mocker.patch("sfkit.utils.sfgwas_protocol.open")
    mocker.patch("sfkit.utils.sfgwas_protocol.tomlkit.dumps")
    mocker.patch("sfkit.utils.sfgwas_protocol.condition_or_fail")
    mocker.patch("sfkit.utils.sfgwas_protocol.to_float_int_or_bool")

    sfgwas_protocol.update_config_global()

    mock_doc_ref_dict["description"] = "TEST"
    sfgwas_protocol.update_config_global()


def test_update_config_global_phase(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.tomlkit.parse", mock_toml_load)
    mocker.patch("sfkit.utils.sfgwas_protocol.open")
    mocker.patch("sfkit.utils.sfgwas_protocol.tomlkit.dumps")

    sfgwas_protocol.update_config_global_phase("1", False)
    sfgwas_protocol.update_config_global_phase("2", False)
    sfgwas_protocol.update_config_global_phase("3", True)


def test_update_sfgwas_go(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.fileinput.input", mock_fileinput_input)

    sfgwas_protocol.update_sfgwas_go()


def test_build_sfgwas(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.os.chdir")
    mocker.patch("sfkit.utils.sfgwas_protocol.run_command")
    mocker.patch("sfkit.utils.sfgwas_protocol.update_firestore")

    sfgwas_protocol.build_sfgwas()


def test_start_sfgwas(mocker):
    mocker.patch("sfkit.utils.sfgwas_protocol.update_firestore")
    mocker.patch("sfkit.utils.sfgwas_protocol.run_sfprotocol_with_task_updates")
    mocker.patch("sfkit.utils.sfgwas_protocol.post_process_results")
    mocker.patch("sfkit.utils.sfgwas_protocol.os.chdir")

    sfgwas_protocol.start_sfgwas("0")
    sfgwas_protocol.start_sfgwas("1")
    sfgwas_protocol.start_sfgwas("2", demo=True, protocol="garbage")

    mocker.patch("sfkit.utils.sfgwas_protocol.constants.IS_DOCKER", True)
    sfgwas_protocol.start_sfgwas("2", demo=True, protocol="garbage")
