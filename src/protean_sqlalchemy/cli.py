"""
Module that contains the command line app.

Why does this file exist, and why not put this in __main__?

  You might be tempted to import things from __main__ later, but that will cause
  problems: the code will get executed twice:

  - When you run `python -mprotean_sqlalchemy` python will execute
    ``__main__.py`` as a script. That means there won't be any
    ``protean_sqlalchemy.__main__`` in ``sys.modules``.
  - When you import __main__ it will get executed again (as a module) because
    there's no ``protean_sqlalchemy.__main__`` in ``sys.modules``.

  Also see (1) from http://click.pocoo.org/5/setuptools/#setuptools-integration
"""
import click

from protean.conf import active_config
from protean.core.repository import repo

from protean_sqlalchemy.repository import SqlalchemySchema


@click.group()
def main():
    """ Utility commands for the Protean Sqlalchemy package """
    pass


@main.command()
def create_tables():
    """ Command to create all tables for registered entities"""
    click.echo('Creating all tables for registered entities')

    # Create all the tables
    for conn_name, conn in repo.connections.items():
        if active_config['REPOSITORIES'][
                conn_name]['PROVIDER'] == 'protean_sqlalchemy.repository':
            SqlalchemySchema.metadata.create_all(conn.bind)


@main.command()
def drop_tables():
    """ Command to drop all tables for registered entities"""
    click.echo('Dropping all tables for registered entities')

    # Delete all the tables
    for conn_name, conn in repo.connections.items():
        if active_config['REPOSITORIES'][
                conn_name]['PROVIDER'] == 'protean_sqlalchemy.repository':
            SqlalchemySchema.metadata.drop_all(conn.bind)
