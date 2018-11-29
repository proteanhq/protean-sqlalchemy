""" Utility functions for the Protean Sqlalchemy Package """

from protean.conf import active_config
from protean.core.repository import repo

from protean_sqlalchemy.repository import SqlalchemySchema


def create_tables():
    """ Create tables for all registered entities"""

    for conn_name, conn in repo.connections.items():
        if active_config.REPOSITORIES[conn_name]['PROVIDER'] ==\
                'protean_sqlalchemy.repository':
            SqlalchemySchema.metadata.create_all(conn.bind)


def drop_tables():
    """ Drop tables for all registered entities"""

    # Delete all the tables
    for conn_name, conn in repo.connections.items():
        if active_config.REPOSITORIES[conn_name]['PROVIDER'] == \
                'protean_sqlalchemy.repository':
            SqlalchemySchema.metadata.drop_all(conn.bind)
