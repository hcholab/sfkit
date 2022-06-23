from google.cloud import firestore
from sftools.protocol.utils import constants
from sftools.protocol.utils.google_cloud_compute import GoogleCloudCompute
from sftools.protocol.utils.google_cloud_pubsub import GoogleCloudPubsub


def auth():
    study_title: str = input("Enter study title (same study title as on the website): ")
    doc_ref = firestore.Client().collection("studies").document(study_title.replace(" ", "").lower())
    doc_ref_dict = doc_ref.get().to_dict() or {}  # type: ignore
    if not doc_ref_dict:  # validate study title
        print("The study you entered was not found.")
        exit(1)

    email: str = input("Enter email (this should be the same email that you use to log in to the website): ")
    if email not in doc_ref_dict["participants"]:  # validate email
        print("The email you entered was not found in the study.")
        exit(1)

    # validate google cloud permissions
    # TODO: review if this is sufficient and necessary?
    print("Validating Google Cloud permissions...")
    gcp_project = doc_ref_dict["personal_parameters"][email]["GCP_PROJECT"]["value"]
    gcloudCompute = GoogleCloudCompute(gcp_project)
    try:
        gcloudCompute.list_instances()
    except Exception as e:
        print("Insufficient permissions your GCP project's Google Cloud Compute API; see below for more information: ")
        print(e)
        exit(1)

    # set up pubsub
    role: str = str(doc_ref_dict["participants"].index(email) + 1)
    gcloudPubsub = GoogleCloudPubsub(constants.SERVER_GCP_PROJECT, role, study_title)
    gcloudPubsub.create_topic_and_subscribe()

    # save the email, study title to a file
    with open("auth.txt", "w") as f:
        f.write(f"{study_title}\n{email}")

    print("You are now authenticated with the sftools CLI!")


def main():
    auth()


if __name__ == "__main__":
    main()
