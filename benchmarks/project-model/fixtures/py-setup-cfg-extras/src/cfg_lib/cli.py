import click
from packaging.version import Version

from cfg_lib import __version__


@click.command()
def main():
    click.echo(str(Version(__version__)))
