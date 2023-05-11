from sfkit.utils import pca_protocol


def test_run_pca_protocol(mocker):
    mocker.patch("sfkit.utils.pca_protocol.install_sfgwas")
    mocker.patch("sfkit.utils.pca_protocol.generate_shared_keys")
    mocker.patch("sfkit.utils.pca_protocol.update_config_local")
    mocker.patch("sfkit.utils.pca_protocol.update_config_global")
    mocker.patch("sfkit.utils.pca_protocol.build_sfgwas")
    mocker.patch("sfkit.utils.pca_protocol.start_sfgwas")

    pca_protocol.run_pca_protocol("1")

    pca_protocol.run_pca_protocol("1", True)

    mocker.patch("sfkit.utils.pca_protocol.constants.IS_DOCKER", True)
    pca_protocol.run_pca_protocol("1")


def test_update_config_local(mocker):
    mocker.patch("sfkit.utils.pca_protocol.tomlkit.parse")
    mocker.patch("sfkit.utils.pca_protocol.shutil.copyfile")
    mocker.patch("sfkit.utils.pca_protocol.open")
    mocker.patch("sfkit.utils.pca_protocol.tomlkit.dumps")

    pca_protocol.update_config_local("0")

    mocker.patch("sfkit.utils.pca_protocol.tomlkit.parse", side_effect=[FileNotFoundError, {}])
    pca_protocol.update_config_local("1")
