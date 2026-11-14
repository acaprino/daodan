from acme_cli.main import Greeting


def test_greeting():
    assert Greeting("x").name == "x"
