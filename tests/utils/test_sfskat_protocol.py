import os

import pytest
import tomlkit
from nacl.encoding import HexEncoder
from nacl.public import PrivateKey

from sfkit.utils import sfskat_protocol

PARTICIPANTS = ["Broad", "a@a.com", "b@b.com"]


def make_doc_ref_dict(public_keys: list) -> dict:
    return {
        "study_id": "study_id",
        "participants": PARTICIPANTS,
        "parameters": {
            "chromosomes": {"value": "21,22"},
            "ancestries": {"value": "eur, AFR"},
            "masks": {"value": "LoF=HC"},
            "max_maf": {"value": 0.01},
            "phenotype_columns": {"value": "phenotype1,phenotype2"},
            "num_cov": {"value": 10},
        },
        "advanced_parameters": {
            "ckks": {"value": "PN14QP436S45"},
            "mpc_num_threads": {"value": "4"},
            "data_bits": {"value": 70},
            "fractional_bits": {"value": 40},
            "probes": {"value": 50},
            "seed": {"value": ""},
        },
        "personal_parameters": {
            participant: {
                "PUBLIC_KEY": {"value": public_keys[i]},
                "IP_ADDRESS": {"value": f"10.0.{i}.10"},
                "PORTS": {
                    "value": ",".join(str(8100 + 1000 * i + 100 * j) for j in range(3))
                },
                "RESULTS_PATH": {"value": "bucket/path"},
                "SEND_RESULTS": {"value": "Yes"},
            }
            for i, participant in enumerate(PARTICIPANTS)
        },
    }


def load_toml(path) -> dict:
    with open(path, "r") as f:
        return tomlkit.parse(f.read()).unwrap()


def test_run_sfskat_protocol(mocker):
    mocker.patch("sfkit.utils.sfskat_protocol.install_sfskat")
    mocker.patch(
        "sfkit.utils.sfskat_protocol.get_doc_ref_dict",
        return_value=make_doc_ref_dict([""] * 3),
    )
    mocker.patch("sfkit.utils.sfskat_protocol.generate_shared_keys")
    mocker.patch("sfkit.utils.sfskat_protocol.update_config", return_value="config_dir")
    mocker.patch("sfkit.utils.sfskat_protocol.sync_with_other_vms")
    mocker.patch("sfkit.utils.sfskat_protocol.start_sfskat")

    sfskat_protocol.run_sfskat_protocol("1", demo=True)
    sfskat_protocol.generate_shared_keys.assert_not_called()

    sfskat_protocol.run_sfskat_protocol("1")
    sfskat_protocol.generate_shared_keys.assert_called_once_with(1, ["EUR", "AFR"])
    sfskat_protocol.start_sfskat.assert_called_with("1", "config_dir")

    mocker.patch("sfkit.utils.sfskat_protocol.constants.IS_DOCKER", True)
    sfskat_protocol.run_sfskat_protocol("1")


def test_install_sfskat(mocker):
    mocker.patch("sfkit.utils.sfskat_protocol.os.chdir")
    mocker.patch("sfkit.utils.sfskat_protocol.run_command")
    mocker.patch("sfkit.utils.sfskat_protocol.update_firestore")
    mocker.patch("sfkit.utils.sfskat_protocol.install_go")
    mocker.patch("sfkit.utils.sfskat_protocol.os.path.isdir", return_value=True)

    sfskat_protocol.install_sfskat()

    mocker.patch("sfkit.utils.sfskat_protocol.os.path.isdir", return_value=False)
    sfskat_protocol.install_sfskat()


def test_parse_params():
    assert sfskat_protocol.parse_list_param("", ["x"]) == ["x"]
    assert sfskat_protocol.parse_list_param(" , ", ["x"]) == ["x"]
    assert sfskat_protocol.parse_list_param("21, 22", []) == ["21", "22"]
    assert sfskat_protocol.parse_ancestries("") == ["EUR"]
    assert sfskat_protocol.parse_ancestries("eur, Afr") == ["EUR", "AFR"]


def test_get_run_dir(mocker, tmp_path):
    mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_DIR", str(tmp_path))
    mocker.patch("sfkit.utils.helper_functions.update_firestore")

    assert sfskat_protocol.get_run_dir("0") == str(tmp_path / "skat_run")
    assert (tmp_path / "skat_run").is_dir()

    (tmp_path / "data_path.txt").write_text(f"{tmp_path}\n")
    assert sfskat_protocol.get_run_dir("1") == str(tmp_path)

    (tmp_path / "data_path.txt").write_text("\n")
    with pytest.raises(SystemExit):
        sfskat_protocol.get_run_dir("2")


def test_generate_shared_keys(mocker, tmp_path):
    mocker.patch("sfkit.utils.sfskat_protocol.update_firestore")
    mocker.patch("sfkit.utils.sfskat_protocol.time.sleep")
    private_keys = [PrivateKey.generate() for _ in PARTICIPANTS]
    doc_ref_dict = make_doc_ref_dict(
        [key.public_key.encode(encoder=HexEncoder).decode() for key in private_keys]
    )

    for role, private_key in enumerate(private_keys):
        sfkit_dir = tmp_path / str(role)
        sfkit_dir.mkdir()
        (sfkit_dir / "my_private_key.txt").write_text(
            private_key.encode(encoder=HexEncoder).decode() + "\n"
        )
        mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_DIR", str(sfkit_dir))
        # the other parties' public keys only show up after one round of waiting
        waiting = make_doc_ref_dict([""] * 3)
        mocker.patch(
            "sfkit.utils.sfskat_protocol.get_doc_ref_dict",
            side_effect=[waiting] + [doc_ref_dict] * 3,
        )
        sfskat_protocol.generate_shared_keys(role, ["EUR", "AFR"])

    def key(role: int, ancestry: str, name: str) -> bytes:
        return (
            tmp_path / str(role) / "skat_shared_keys" / ancestry / name
        ).read_bytes()

    # each party holds exactly the keys that `secure-rvas party` loads
    expected = {
        0: ["shared_key_0_1.bin", "shared_key_0_2.bin", "shared_key_global.bin"],
        1: ["shared_key_0_1.bin", "shared_key_1_2.bin", "shared_key_global.bin"],
        2: ["shared_key_0_2.bin", "shared_key_1_2.bin", "shared_key_global.bin"],
    }
    for ancestry in ["EUR", "AFR"]:
        for role, names in expected.items():
            assert (
                sorted(os.listdir(tmp_path / str(role) / "skat_shared_keys" / ancestry))
                == names
            )
            assert all(len(key(role, ancestry, name)) == 32 for name in names)
        # both holders of a key derive the same bytes
        assert key(0, ancestry, "shared_key_0_1.bin") == key(
            1, ancestry, "shared_key_0_1.bin"
        )
        assert key(0, ancestry, "shared_key_0_2.bin") == key(
            2, ancestry, "shared_key_0_2.bin"
        )
        assert key(1, ancestry, "shared_key_1_2.bin") == key(
            2, ancestry, "shared_key_1_2.bin"
        )
        assert (
            len({key(role, ancestry, "shared_key_global.bin") for role in expected})
            == 1
        )
        assert (
            len(
                {key(0, ancestry, name) for name in expected[0]}
                | {key(1, ancestry, "shared_key_1_2.bin")}
            )
            == 4
        )
    assert key(0, "EUR", "shared_key_0_1.bin") != key(0, "AFR", "shared_key_0_1.bin")
    assert key(0, "EUR", "shared_key_global.bin") != key(
        0, "AFR", "shared_key_global.bin"
    )


def test_update_config(mocker, tmp_path):
    mocker.patch(
        "sfkit.utils.sfskat_protocol.get_doc_ref_dict",
        return_value=make_doc_ref_dict([""] * 3),
    )
    mocker.patch("sfkit.utils.sfskat_protocol.update_firestore")
    mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_DIR", str(tmp_path))
    mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_PROXY_ON", False)
    mocker.patch("sfkit.utils.sfskat_protocol.os.cpu_count", return_value=8)
    data_path = tmp_path / "run_dir"
    data_path.mkdir()
    (tmp_path / "data_path.txt").write_text(f"{data_path}\n")
    chr_dir = f"{data_path}/prepared/{{ancestry}}/chr{{chromosome}}"

    config_dir = sfskat_protocol.update_config("1")
    assert config_dir == str(tmp_path / "skat_config")
    assert load_toml(os.path.join(config_dir, "configGlobal.toml")) == {
        "run_dir": str(data_path),
        "chromosomes": [21, 22],
        "phenotype_columns": ["phenotype1", "phenotype2"],
        "ancestries": ["EUR", "AFR"],
        "num_cov": 10,
        "ckks": "PN14QP436S45",
        "mpc_num_threads": 4,
        "data_bits": 70,
        "fractional_bits": 40,
        "probes": 50,
        "seed": 42,
        "binding_ipaddr": "0.0.0.0",
        "servers": {
            "party0": {
                "ipaddr": "10.0.0.10",
                "ports": {"party1": "8200", "party2": "8300"},
            },
            "party1": {
                "ipaddr": "10.0.1.10",
                "ports": {"party0": "9100", "party2": "9300"},
            },
            "party2": {
                "ipaddr": "10.0.2.10",
                "ports": {"party0": "10100", "party1": "10200"},
            },
        },
    }
    assert load_toml(os.path.join(config_dir, "configLocal.Party1.toml")) == {
        "shared_keys_path": str(tmp_path / "skat_shared_keys"),
        "local_num_threads": 8,
        "genotype_dir": f"{chr_dir}/A/geno",
        "phenotype_file": f"{chr_dir}/A/pheno.txt",
        "covariate_file": f"{chr_dir}/A/cov.txt",
        "genes_file": f"{chr_dir}/genes.txt",
        "variant_counts_file": f"{chr_dir}/block_sizes.txt",
    }

    sfskat_protocol.update_config("2")
    assert load_toml(os.path.join(config_dir, "configLocal.Party2.toml")) == {
        "shared_keys_path": str(tmp_path / "skat_shared_keys"),
        "local_num_threads": 8,
        "genotype_dir": f"{chr_dir}/B/geno",
        "private_genotype_dir": f"{chr_dir}/B/private",
        "phenotype_file": f"{chr_dir}/B/pheno.txt",
        "covariate_file": f"{chr_dir}/B/cov.txt",
        "genes_file": f"{chr_dir}/genes.txt",
        "variant_counts_file": f"{chr_dir}/block_sizes.txt",
    }

    # the auxiliary party has no data, and the proxy makes every peer local
    mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_PROXY_ON", True)
    sfskat_protocol.update_config("0")
    assert load_toml(os.path.join(config_dir, "configLocal.Party0.toml")) == {
        "shared_keys_path": str(tmp_path / "skat_shared_keys"),
        "local_num_threads": 8,
    }
    global_config = load_toml(os.path.join(config_dir, "configGlobal.toml"))
    assert global_config["run_dir"] == str(tmp_path / "skat_run")
    assert {server["ipaddr"] for server in global_config["servers"].values()} == {
        "127.0.0.1"
    }


def test_start_sfskat(mocker):
    mocker.patch("sfkit.utils.sfskat_protocol.update_firestore")
    mocker.patch("sfkit.utils.sfskat_protocol.boot_sfkit_proxy")
    mocker.patch("sfkit.utils.sfskat_protocol.run_command")
    mocker.patch("sfkit.utils.sfskat_protocol.process_output_files")
    mocker.patch("sfkit.utils.sfskat_protocol.constants.IS_DOCKER", True)

    mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_PROXY_ON", True)
    sfskat_protocol.start_sfskat("1", "config_dir")
    sfskat_protocol.boot_sfkit_proxy.assert_called_once_with(
        "1", "config_dir/configGlobal.toml"
    )
    sfskat_protocol.boot_sfkit_proxy.return_value.terminate.assert_called_once()
    sfskat_protocol.run_command.assert_called_once_with(
        ["secure-rvas", "party", "--config", "config_dir", "--party", "1"],
        fail_message="Failed SF-SKAT protocol",
        role="1",
    )
    sfskat_protocol.process_output_files.assert_called_once_with("1")

    mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_PROXY_ON", False)
    mocker.patch("sfkit.utils.sfskat_protocol.constants.IS_DOCKER", False)
    mocker.patch("sfkit.utils.sfskat_protocol.constants.IS_INSTALLED_VIA_SCRIPT", False)
    sfskat_protocol.start_sfskat("2", "config_dir")
    assert sfskat_protocol.run_command.call_args.args[0][0] == os.path.join(
        "sf-skat", "secure-rvas"
    )
    sfskat_protocol.boot_sfkit_proxy.assert_called_once()
    sfskat_protocol.process_output_files.assert_called_once()


def test_process_output_files(mocker, tmp_path):
    mocker.patch(
        "sfkit.utils.sfskat_protocol.get_doc_ref_dict",
        return_value=make_doc_ref_dict([""] * 3),
    )
    mocker.patch("sfkit.utils.sfskat_protocol.update_firestore")
    mocker.patch("sfkit.utils.sfskat_protocol.constants.SFKIT_DIR", str(tmp_path))
    mocker.patch("sfkit.utils.sfskat_protocol.copy_to_out_folder")
    mocker.patch("sfkit.utils.sfskat_protocol.copy_results_to_cloud_storage")
    mocker.patch("sfkit.utils.sfskat_protocol.website_send_file")
    (tmp_path / "data_path.txt").write_text(f"{tmp_path}\n")
    (tmp_path / "secure" / "EUR").mkdir(parents=True)
    (tmp_path / "secure" / "EUR" / "all_secure_results.tsv").write_text("results\n")

    sfskat_protocol.process_output_files("1")

    secure_dir = str(tmp_path / "secure")
    sfskat_protocol.copy_to_out_folder.assert_called_once_with(
        [secure_dir, str(tmp_path / "metrics")]
    )
    sfskat_protocol.copy_results_to_cloud_storage.assert_called_once_with(
        "1", "bucket/path", secure_dir
    )
    # only EUR has results; AFR is skipped
    sfskat_protocol.website_send_file.assert_called_once()
    assert (
        sfskat_protocol.website_send_file.call_args.args[1]
        == "EUR_all_secure_results.tsv"
    )
