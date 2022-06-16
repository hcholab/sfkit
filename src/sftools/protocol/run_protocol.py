import sys

from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_compute import GoogleCloudCompute
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def create_instance_name(study_title: str, role: str) -> str:
    return f"{study_title.replace(' ', '').lower()}-{constants.INSTANCE_NAME_ROOT}{role}"


def run_protocol(study_title: str, email: str, num_cpus=4, boot_disk_size=10) -> bool:
    db = firestore.Client()
    doc_ref = db.collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict: dict = doc_ref.get().to_dict()  # type: ignore
    user_id: str = email
    role: str = str(doc_ref_dict["participants"].index(user_id) + 1)
    gcp_project: str = doc_ref_dict["personal_parameters"][user_id]["GCP_PROJECT"]["value"]
    statuses: dict = doc_ref_dict["status"]

    if statuses[user_id] in ["['']", "['validating']", "['invalid data']"]:
        print("You have not successfully validated your data.  Please do so before proceeding.")
        return False

    if statuses[user_id] == ["not ready"]:
        statuses[user_id] = ["ready"]
        personal_parameters = doc_ref_dict["personal_parameters"]
        personal_parameters[user_id]["NUM_CPUS"]["value"] = num_cpus
        personal_parameters[user_id]["NUM_THREADS"]["value"] = num_cpus
        personal_parameters[user_id]["BOOT_DISK_SIZE"]["value"] = boot_disk_size
        doc_ref.set(
            {
                "status": statuses,
                "personal_parameters": personal_parameters,
            },
            merge=True,
        )  # type: ignore

    if any(s in str(statuses.values()) for s in ["['']", "['validating']", "['invalid data']", "['not ready']"]):
        print("The other participant is not yet ready.  Please try again once they are.")
        return False
    elif statuses[user_id] == ["ready"]:
        statuses[user_id] = ["Setting up your vm instance..."]
        doc_ref.set({"status": statuses}, merge=True)  # type: ignore
        doc_ref_dict = doc_ref.get().to_dict()  # type: ignore

        gcloudCompute = GoogleCloudCompute(gcp_project)
        instance: str = create_instance_name(study_title, role)
        vm_parameters = doc_ref_dict["personal_parameters"][user_id]
        gcloudCompute.setup_instance(
            constants.SERVER_ZONE,
            instance,
            role,
            {"key": "data_path", "value": vm_parameters["DATA_PATH"]["value"]},
            vm_parameters["NUM_CPUS"]["value"],
            boot_disk_size=vm_parameters["BOOT_DISK_SIZE"]["value"],
        )

        # Give instance publish access to pubsub for status updates
        member: str = f"serviceAccount:{gcloudCompute.get_service_account_for_vm(constants.SERVER_ZONE, instance)}"
        gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
        gcloudPubsub.add_pub_iam_member("roles/pubsub.publisher", member)

        if role == "1":
            print("Asking cp0 to set up their part as well...")
            gcloudPubsub.publish(f"run_protocol_for_cp0::{study_title}::{member}::{user_id}")

    print("Set up is complete!  Your GWAS is now running.")
    return True


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        run_protocol("Alpha", "a@a.com")
    else:
        study_title = input("Enter study title: ")
        email = input("Enter email (this should be the same email that you use to log in to the website): ")
        run_protocol(study_title, email)


if __name__ == "__main__":
    main()
