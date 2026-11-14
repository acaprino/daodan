import pytest

from hatch_demo.show import show


def test_show(capsys):
    show("x")
    assert capsys.readouterr().out
