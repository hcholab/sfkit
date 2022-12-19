# sourcery skip: require-parameter-annotation, require-return-annotation
from io import StringIO
import requests

from sfkit import api


def test_website_send_file(mocker):
    mocker.patch("sfkit.api.requests.post", mock_get_post)
    mocker.patch("sfkit.api.open")

    res = api.website_send_file(StringIO("web"), "msg")
    assert res == True


def test_website_get(mocker):
    mocker.patch("sfkit.api.requests.get", mock_get_post)
    mocker.patch("sfkit.api.open")

    res = api.website_get("web")

    assert res.status_code == 200
    assert res.url == "https://sfkit.org/web"


def test_get_doc_ref_dict(mocker):
    mocker.patch("sfkit.api.website_get", mock_website_get)
    res = api.get_doc_ref_dict()
    assert res == {"get_doc_ref_dict": "get_doc_ref_dict"}


def test_get_username(mocker):
    mocker.patch("sfkit.api.website_get", mock_website_get)
    res = api.get_username()
    assert res == ""


def test_update_firestore(mocker):
    mocker.patch("sfkit.api.website_get", mock_website_get)
    res = api.update_firestore("msg")
    assert res == True


def test_create_cp0(mocker):
    mocker.patch("sfkit.api.website_get", mock_website_get)
    res = api.create_cp0()
    assert res == True


def mock_get_post(url, headers, params=None, files=None):
    res = requests.Response()
    res.status_code = 200
    res.url = url
    res.headers = headers
    res._content = ('{"' + url + '": "' + url + '"}').encode()
    return res


def mock_website_get(request_type: str, params: dict = dict()) -> requests.Response:
    return mock_get_post(request_type, {}, params)
