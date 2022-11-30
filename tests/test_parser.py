from pytest_mock import MockFixture

from sfkit import parser


def test_get_parser(mocker: MockFixture) -> None:
    parser.get_parser()
