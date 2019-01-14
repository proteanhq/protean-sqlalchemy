""" Utility functions for the Protean Sqlalchemy Package """
from protean.core.repository import repo_factory
from sqlalchemy.orm.session import Session

from protean_sqlalchemy.repository import SqlalchemyModel


def create_tables():
    """ Create tables for all registered entities"""

    for conn_name, conn in repo_factory.connections.items():
        if isinstance(conn, Session):
            SqlalchemyModel.metadata.create_all(conn.bind)


def drop_tables():
    """ Drop tables for all registered entities"""

    # Delete all the tables
    for conn_name, conn in repo_factory.connections.items():
        if isinstance(conn, Session):
            SqlalchemyModel.metadata.drop_all(conn.bind)
