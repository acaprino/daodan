import attrs
import click


@attrs.define
class Greeting:
    name: str


@click.command()
@click.argument("name")
def cli(name):
    click.echo(f"hello {Greeting(name).name}")
