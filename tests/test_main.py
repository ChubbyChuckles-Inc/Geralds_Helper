from __future__ import annotations

import pytest

from src.main import main


def test_main(capsys: "pytest.CaptureFixture[str]") -> None:
    """Ensure the entry point prints the bootstrap confirmation."""
    exit_code = main()
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Table Tennis Team Manager bootstrap successful." in captured.out
