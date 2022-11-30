# sourcery skip: docstrings-for-classes, require-parameter-annotation, require-return-annotation
from sfkit import cli
from pytest_mock import MockFixture


def test_main(mocker: MockFixture) -> None:
    mocker.patch("sfkit.cli.get_parser", mock_get_parser)
    mocker.patch("sfkit.cli.auth")
    mocker.patch("sfkit.cli.setup_networking")
    mocker.patch("sfkit.cli.generate_personal_keys")
    mocker.patch("sfkit.cli.register_data")
    mocker.patch("sfkit.cli.run_protocol")

    cli.main()
    MockArgs.command = "networking"
    cli.main()
    MockArgs.command = "generate_keys"
    cli.main()
    MockArgs.command = "register_data"
    cli.main()
    MockArgs.command = "run_protocol"
    cli.main()
    MockArgs.command = "other"
    cli.main()


def mock_get_parser():
    class Parser:
        def parse_args(self):
            return MockArgs()

        def print_help(self):
            pass

    return Parser()


class MockArgs:
    command: str = "auth"
    ports: str = ""
    geno_binary_file_prefix: str = ""
    data_path: str = ""
    phase: str = ""
    demo: bool = False
