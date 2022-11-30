# sourcery skip: avoid-global-variables, camel-case-classes, docstrings-for-classes, require-parameter-annotation, require-return-annotation
import copy


def mock_sleep(seconds: int):
    mock_doc_ref_dict["personal_parameters"]["a@a.com"]["PUBLIC_KEY"]["value"] = "public_key"
    mock_doc_ref_dict["personal_parameters"]["b@b.com"]["PUBLIC_KEY"]["value"] = "public_key"
    mock_doc_ref_dict["personal_parameters"]["Broad"]["PUBLIC_KEY"]["value"] = "public_key"

    mock_doc_ref_dict["personal_parameters"]["a@a.com"]["IP_ADDRESS"]["value"] = "127.0.0.1"


def mock_get_doc_ref_dict() -> dict:
    return mock_doc_ref_dict


toml_load_true = False


def mock_toml_load(path):
    if toml_load_true or "good" in path:
        return mock_toml_data
    raise FileNotFoundError


def mock_copyfile(src, dest):
    global toml_load_true
    toml_load_true = True


def mock_fileinput_input(files, inplace):
    return ["line1", "CONFIG_PATH = happy", "line3", "NUM_INDS"]


mock_doc_ref_dict = {
    "personal_parameters": {
        "a@a.com": {
            "PUBLIC_KEY": {"value": ""},
            "NUM_INDS": {"value": 1},
            "IP_ADDRESS": {"value": "127.0.0.1"},
            "PORTS": {"value": "80,80,80"},
            "DATA_HASH": {"value": "data_hash"},
        },
        "Broad": {
            "PUBLIC_KEY": {"value": ""},
            "NUM_INDS": {"value": 1},
            "IP_ADDRESS": {"value": "127.0.0.1"},
            "PORTS": {"value": "80,80,80"},
            "DATA_HASH": {"value": "data_hash"},
        },
        "b@b.com": {
            "PUBLIC_KEY": {"value": ""},
            "NUM_INDS": {"value": 1},
            "IP_ADDRESS": {"value": "127.0.0.1"},
            "PORTS": {"value": "80,80,80"},
            "DATA_HASH": {"value": "data_hash"},
        },
    },
    "parameters": {"num_columns": {"value": 1}, "NUM_SNPS": {"value": 1}, "num_snps": {"value": 1}},
    "participants": ["Broad", "a@a.com", "b@b.com"],
    "advanced_parameters": {},
    "study_type": "SFGWAS",
    "status": {"Broad": "", "a@a.com": "", "b@b.com": ""},
}

mock_doc_ref_dict_keys = copy.deepcopy(mock_doc_ref_dict)
mock_doc_ref_dict_keys["personal_parameters"]["a@a.com"]["PUBLIC_KEY"]["value"] = "public_key"
mock_doc_ref_dict_keys["personal_parameters"]["b@b.com"]["PUBLIC_KEY"]["value"] = "public_key"
mock_doc_ref_dict_keys["personal_parameters"]["Broad"]["PUBLIC_KEY"]["value"] = "public_key"

mock_doc_ref_dict_mpcgwas = copy.deepcopy(mock_doc_ref_dict)
mock_doc_ref_dict_mpcgwas["study_type"] = "MPCGWAS"

mock_doc_ref_dict_pca = copy.deepcopy(mock_doc_ref_dict)
mock_doc_ref_dict_pca["study_type"] = "PCA"

mock_toml_data = {
    "shared_key_path": "",
    "output_dir": "",
    "cache_dir": "",
    "geno_binary_file_prefix": "",
    "geno_block_size_file": "",
    "pheno_file": "",
    "covar_file": "",
    "snp_position_file": "",
    "sample_keep_file": "",
    "snp_ids_file": "",
    "geno_count_file": "",
    "num_main_parties": 2,
    "num_columns": 1,
    "servers": {
        "party0": {"ipaddr": "127.0.0.1", "ports": {"party0": 5000}},
    },
}


def undo_mock_changes():
    global toml_load_true
    toml_load_true = False

    mock_doc_ref_dict["personal_parameters"]["a@a.com"]["PUBLIC_KEY"]["value"] = ""
    mock_doc_ref_dict["personal_parameters"]["b@b.com"]["PUBLIC_KEY"]["value"] = ""
    mock_doc_ref_dict["personal_parameters"]["Broad"]["PUBLIC_KEY"]["value"] = ""


class Mock_Subprocess:
    def __init__(self, returncode):
        self.returncode = returncode


def mock_subprocess_run(command, shell=True):
    if "bad" in command and mock_doc_ref_dict["personal_parameters"]["a@a.com"]["IP_ADDRESS"]["value"] == "bad":
        return Mock_Subprocess(1)
    return Mock_Subprocess(0)
