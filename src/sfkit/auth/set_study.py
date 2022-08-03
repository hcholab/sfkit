### DEPRECATED ###


from google.cloud import firestore
from sfkit.protocol.utils import constants


def set_study():
    with open(constants.AUTH_FILE, "r") as f:
        email = f.readline().rstrip()

    print(f"You are using the following email: {email}")
    print("(If you would like to change this, please rerun `sfkit auth`)\n")
    collection = firestore.Client().collection("studies")
    doc_options = [doc.id for doc in collection.stream() if email in doc.to_dict()["participants"]]  # type: ignore

    if not doc_options:
        print("You are not a participant of any study.")
        return

    print("Here are the studies you are a part of:")
    for i, v in enumerate(doc_options):
        print(f"({i}): {v}")
        print()

    study_index = int(input("Please enter the number of the study you want to use: "))
    if study_index not in range(len(doc_options)):
        print("Invalid study index.")
        return
    study_title = doc_options[study_index]

    with open(constants.AUTH_FILE, "w") as f:
        f.write(email + "\n")
        f.write(study_title + "\n")
    print(f"\nSuccessfully set study to {study_title}!")


def main():
    set_study()


if __name__ == "__main__":
    main()
