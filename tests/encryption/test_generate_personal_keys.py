# sourcery skip: require-parameter-annotation, require-return-annotation
from sfkit.encryption import generate_personal_keys


def test_generate_personal_keys(mocker):
    # mock authenticate_user
    mocker.patch("sfkit.encryption.generate_personal_keys.authenticate_user")
    # mock os.makedirs
    mocker.patch("sfkit.encryption.generate_personal_keys.os.makedirs")
    # mock open
    mocker.patch("sfkit.encryption.generate_personal_keys.open")
    # mock update_firestore
    mocker.patch("sfkit.encryption.generate_personal_keys.update_firestore")

    generate_personal_keys.generate_personal_keys()
