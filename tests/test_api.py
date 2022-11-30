# sourcery skip: require-parameter-annotation, require-return-annotation
import requests

from sfkit import api

# from sfkit.api import website_get


def test_website_get(mocker):
    mocker.patch("sfkit.api.requests.get")
    mocker.patch("sfkit.api.open")
    api.website_get("web").status_code
