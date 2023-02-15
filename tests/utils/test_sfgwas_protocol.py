# # sourcery skip: avoid-global-variables, no-relative-imports, no-wildcard-imports, require-parameter-annotation, require-return-annotation
# from sfkit.utils import sfgwas_protocol
# from tests.helper_functions_and_constants import *


# def test_run_sfgwas_protocol(mocker):
#     mocker.patch("sfkit.utils.sfgwas_protocol.install_sfgwas")
#     mocker.patch("sfkit.utils.sfgwas_protocol.generate_shared_keys")
#     # mock update_config_local
#     mocker.patch("sfkit.utils.sfgwas_protocol.update_config_local")
#     # mock update_config_global
#     mocker.patch("sfkit.utils.sfgwas_protocol.update_config_global")
#     # mock update_config_global_phase
#     mocker.patch("sfkit.utils.sfgwas_protocol.update_config_global_phase")
#     # mock update_sfgwas_go
#     mocker.patch("sfkit.utils.sfgwas_protocol.update_sfgwas_go")
#     # mock build_sfgwas
#     mocker.patch("sfkit.utils.sfgwas_protocol.build_sfgwas")
#     # mock start_sfgwas
#     mocker.patch("sfkit.utils.sfgwas_protocol.start_sfgwas")

#     sfgwas_protocol.run_sfgwas_protocol("1", demo=True)
#     # assert generate_shared_keys function was not called
#     sfgwas_protocol.generate_shared_keys.assert_not_called()

#     sfgwas_protocol.run_sfgwas_protocol("1")
#     # assert generate_shared_keys function was called
#     sfgwas_protocol.generate_shared_keys.assert_called_once()


# def test_install_sfgwas(mocker):
#     mocker.patch("sfkit.utils.sfgwas_protocol.run_command")
#     # mock update_firestore
#     mocker.patch("sfkit.utils.sfgwas_protocol.update_firestore")

#     sfgwas_protocol.install_sfgwas()

#     mocker.patch("sfkit.utils.sfgwas_protocol.os.path.isdir", return_value=True)
#     sfgwas_protocol.install_sfgwas()


# def test_generate_shared_keys(mocker):
#     undo_mock_changes()
#     mocker.patch("sfkit.utils.sfgwas_protocol.get_doc_ref_dict", mock_get_doc_ref_dict)
#     mocker.patch("sfkit.utils.sfgwas_protocol.open")
#     mocker.patch("sfkit.utils.sfgwas_protocol.time.sleep", mock_sleep)
#     mocker.patch("sfkit.utils.sfgwas_protocol.PrivateKey")
#     mocker.patch("sfkit.utils.sfgwas_protocol.PublicKey")
#     mocker.patch("sfkit.utils.sfgwas_protocol.condition_or_fail")
#     mocker.patch("sfkit.utils.sfgwas_protocol.Box")

#     sfgwas_protocol.generate_shared_keys(0)
#     undo_mock_changes()
#     sfgwas_protocol.generate_shared_keys(1)


# def test_update_config_local(mocker):
#     mocker.patch("sfkit.utils.sfgwas_protocol.toml.load", mock_toml_load)
#     mocker.patch("sfkit.utils.sfgwas_protocol.shutil.copyfile", mock_copyfile)
#     mocker.patch("sfkit.utils.sfgwas_protocol.update_data_file_paths")
#     mocker.patch("sfkit.utils.sfgwas_protocol.open")
#     mocker.patch("sfkit.utils.sfgwas_protocol.toml.dump")

#     sfgwas_protocol.update_config_local("0", "good path")
#     sfgwas_protocol.update_config_local("1", "bad path")


# def test_update_data_file_paths(mocker):
#     mocker.patch("sfkit.utils.sfgwas_protocol.open")

#     sfgwas_protocol.update_data_file_paths(mock_toml_data)


# # def test_update_config_global(mocker):
# #     # mock get_doc_ref_dict
# #     mocker.patch("sfkit.utils.sfgwas_protocol.get_doc_ref_dict", mock_get_doc_ref_dict)
# #     # mock toml.load
# #     mocker.patch("sfkit.utils.sfgwas_protocol.toml.load", mock_toml_load)
# #     # mock open
# #     mocker.patch("sfkit.utils.sfgwas_protocol.open")
# #     # mock toml.dump
# #     mocker.patch("sfkit.utils.sfgwas_protocol.toml.dump")
# #     # mock condition_or_fail
# #     mocker.patch("sfkit.utils.sfgwas_protocol.condition_or_fail")

# #     sfgwas_protocol.update_config_global()


# def test_update_config_global_phase(mocker):
#     # mock toml.load
#     mocker.patch("sfkit.utils.sfgwas_protocol.toml.load", mock_toml_load)
#     # mock open
#     mocker.patch("sfkit.utils.sfgwas_protocol.open")
#     # mock toml.dump
#     mocker.patch("sfkit.utils.sfgwas_protocol.toml.dump")

#     sfgwas_protocol.update_config_global_phase("1", False)
#     sfgwas_protocol.update_config_global_phase("2", False)
#     sfgwas_protocol.update_config_global_phase("3", True)


# def test_update_sfgwas_go(mocker):
#     # mock fileinput.input
#     mocker.patch("sfkit.utils.sfgwas_protocol.fileinput.input", mock_fileinput_input)

#     sfgwas_protocol.update_sfgwas_go()


# def test_build_sfgwas(mocker):
#     # mock run_command
#     mocker.patch("sfkit.utils.sfgwas_protocol.run_command")
#     # mock update_firestore
#     mocker.patch("sfkit.utils.sfgwas_protocol.update_firestore")

#     sfgwas_protocol.build_sfgwas()


# # def test_start_sfgwas(mocker):
# #     # mock update_firestore
# #     mocker.patch("sfkit.utils.sfgwas_protocol.update_firestore")
# #     # mock run_command
# #     mocker.patch("sfkit.utils.sfgwas_protocol.run_command")
# #     # mock open
# #     mocker.patch("sfkit.utils.sfgwas_protocol.open")
# #     # mock shutil.make_archive
# #     mocker.patch("sfkit.utils.sfgwas_protocol.shutil.make_archive")
# #     # mock website_send_file
# #     mocker.patch("sfkit.utils.sfgwas_protocol.website_send_file")

# #     sfgwas_protocol.start_sfgwas("1")
# #     sfgwas_protocol.start_sfgwas("2", protocol="PCA")
# #     sfgwas_protocol.start_sfgwas("2", demo=True, protocol="garbage")

# #     sfgwas_protocol.start_sfgwas("1", demo=True)
# #     sfgwas_protocol.start_sfgwas("2", protocol="PCA", demo=True)
