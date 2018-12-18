""" Utility functions for the Protean Sqlalchemy Package """
from protean.core.repository import repo
from sqlalchemy.orm.session import Session

from protean_sqlalchemy.repository import SqlalchemySchema


def create_tables():
    """ Create tables for all registered entities"""

    for conn_name, conn in repo.connections.items():
        if isinstance(conn, Session):
            SqlalchemySchema.metadata.create_all(conn.bind)


def drop_tables():
    """ Drop tables for all registered entities"""

    # Delete all the tables
    for conn_name, conn in repo.connections.items():
        if isinstance(conn, Session):
            SqlalchemySchema.metadata.drop_all(conn.bind)
