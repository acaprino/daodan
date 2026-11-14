import click

from ws_core.model import Item


@click.command()
def main():
    click.echo(Item("a-1").sku)
