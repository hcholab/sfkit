import sys

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_compute import GoogleCloudCompute
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub
from sftools.protocol.utils.google_cloud_storage import GoogleCloudStorage
from sftools.protocol.utils.utils import create_instance_name


def validate_data() -> bool:
    with open("auth.txt", "r") as f:
        study_title = f.readline()
        email = f.readline().rstrip()
    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email) + 1)
    gcp_project = doc_ref_dict["personal_parameters"][email]["GCP_PROJECT"]["value"]
    data_path = doc_ref_dict["personal_parameters"][email]["DATA_PATH"]["value"]
    if not gcp_project or gcp_project == "" or not data_path or data_path == "":
        print("Before you can start the study, you need to set your GCP project and data path on the website.")
        return False
    gcloudStorage = GoogleCloudStorage(gcp_project)
    files = gcloudStorage.list_files_in_path(data_path)
    if any(desired_file not in files for desired_file in constants.DATA_VALIDATION_FILES):
        print("The data you uploaded is missing some files. Please check that you uploaded all the data files")
        return False
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.publish(f"update_firestore::status=not ready::{study_title}::{email}")
    print("Successfully validated data!")
    return True


def main():
    pass


if __name__ == "__main__":
    main()
