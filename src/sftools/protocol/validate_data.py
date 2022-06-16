import sys
from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_compute import GoogleCloudCompute
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def create_instance_name(study_title: str, role: str) -> str:
    return f"{study_title.replace(' ', '').lower()}-{constants.INSTANCE_NAME_ROOT}{role}"


def validate_data(study_title: str, email: str) -> bool:
    db = firestore.Client()
    doc_ref = db.collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    role: str = str(doc_ref_dict["participants"].index(email) + 1)
    gcp_project = doc_ref_dict["personal_parameters"][email]["GCP_PROJECT"]["value"]
    data_path = doc_ref_dict["personal_parameters"][email]["DATA_PATH"]["value"]
    if not gcp_project or gcp_project == "" or not data_path or data_path == "":
        print("Before you can start the study, you need to set your GCP project and data path on the website.")
        return False
    statuses = doc_ref_dict["status"]
    statuses[email] = ["validating"]
    doc_ref.set({"status": statuses}, merge=True)  # type: ignore

    gcloudCompute = GoogleCloudCompute(gcp_project)
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)

    gcloudPubsub.create_topic_and_subscribe()
    instance = create_instance_name(study_title, role)
    gcloudCompute.setup_networking(doc_ref_dict, role)
    gcloudCompute.setup_instance(
        constants.SERVER_ZONE, instance, role, {"key": "data_path", "value": data_path}, validate=True
    )

    # Give instance publish access to pubsub for status updates
    member = f"serviceAccount:{gcloudCompute.get_service_account_for_vm(constants.SERVER_ZONE, instance)}"

    gcloudPubsub.add_pub_iam_member("roles/pubsub.publisher", member)

    if role == "1":
        print("Asking cp0 to set up their networking as well...")
        gcloudPubsub.publish(f"validate_data_for_cp0::{study_title}")

    print("Data validation should now be in progress...")
    return True


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        validate_data("Alpha", "a@a.com")
    else:
        study_title = input("Enter study title: ")
        email = input("Enter email (this should be the same email that you use to log in to the website): ")
        validate_data(study_title, email)


if __name__ == "__main__":
    main()
