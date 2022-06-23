from sftools.protocol.utils import constants


def create_instance_name(study_title: str, role: str) -> str:
    return f"{study_title.replace(' ', '').lower()}-{constants.INSTANCE_NAME_ROOT}{role}"
