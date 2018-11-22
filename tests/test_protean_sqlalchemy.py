
from click.testing import CliRunner

from protean_sqlalchemy.cli import main


def test_main():
    runner = CliRunner()
    result = runner.invoke(main, [])

    assert 'Utility commands for the Protean Sqlalchemy package' in result.output
    assert result.exit_code == 0
