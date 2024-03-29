# sourcery skip: require-parameter-annotation, require-return-annotation
from io import StringIO
from requests import Response

from sfkit import api


def test_website_send_file(mocker):
    mocker.patch("sfkit.api.requests.post", mock_get_post)
    mocker.patch("sfkit.api.open")
    mocker.patch("sfkit.api.get_service_account_headers", return_value={})

    res = api.website_send_file(StringIO("web"), "msg")
    assert res == True


def test_website_get(mocker):
    mocker.patch("sfkit.api.requests.get", mock_get_post)
    mocker.patch("sfkit.api.open")
    mocker.patch("sfkit.api.get_service_account_headers", return_value={})

    res = api.send_request("web")

    assert res.status_code == 200
    assert res.url == "https://sfkit-website-bhj5a4wkqa-uc.a.run.app/api/web"


def test_get_doc_ref_dict(mocker):
    mocker.patch("sfkit.api.send_request", mock_send_request)
    res = api.get_doc_ref_dict()
    assert res == {"get_doc_ref_dict": "get_doc_ref_dict"}


def test_get_username(mocker):
    mocker.patch("sfkit.api.send_request", mock_send_request)
    res = api.get_username()
    assert res == ""


def test_update_firestore(mocker):
    mocker.patch("sfkit.api.send_request", mock_send_request)
    res = api.update_firestore("msg")
    assert res == True


def test_create_cp0(mocker):
    mocker.patch("sfkit.api.send_request", mock_send_request)
    res = api.create_cp0()
    assert res == True


def mock_get_post(url, headers, params=None, files=None):
    res = Response()
    res.status_code = 200
    res.url = url
    res.headers = headers
    res._content = ('{"' + url + '": "' + url + '"}').encode()
    return res


def mock_send_request(request_type: str, params: dict = dict(), method: str = "GET") -> Response:
    return mock_get_post(request_type, {}, params)
