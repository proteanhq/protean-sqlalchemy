"""This module holds the Provider Implementation for SQLAlchemy"""
from typing import Any

from protean.core.provider.base import BaseProvider
from protean.core.repository import BaseLookup
from sqlalchemy import MetaData
from sqlalchemy import create_engine
from sqlalchemy import orm
from sqlalchemy.engine.url import make_url

from protean_sqlalchemy.repository import SARepository
from protean_sqlalchemy.repository import SqlalchemyModel


class SAProvider(BaseProvider):
    """Provider Implementation class for SQLAlchemy"""

    def __init__(self, *args, **kwargs):
        """Initialize and maintain Engine"""
        super().__init__(*args, **kwargs)

        self._engine = create_engine(make_url(self.conn_info['DATABASE_URI']))
        self._metadata = MetaData(bind=self._engine)

        self._model_classes = {}

    def get_session(self):
        """Establish a session to the Database"""
        # Create the session
        session_factory = orm.sessionmaker(bind=self._engine)
        session_cls = orm.scoped_session(session_factory)

        return session_cls

    def get_connection(self, session_cls=None):
        """ Create the connection to the Database instance"""
        # If this connection has to be created within an existing session,
        #   ``session_cls`` will be provided as an argument.
        #   Otherwise, fetch a new ``session_cls`` from ``get_session()``
        if session_cls is None:
            session_cls = self.get_session()

        return session_cls()

    def close_connection(self, conn):
        """ Close the connection to the Database instance """
        conn.close()

    def get_model(self, entity_cls):
        """Return a fully-baked Model class for a given Entity class"""
        model_cls = None

        if entity_cls.meta_.schema_name in self._model_classes:
            model_cls = self._model_classes[entity_cls.meta_.schema_name]
        else:
            attrs = {
                'entity_cls': entity_cls,
                'metadata': self._metadata
            }
            model_cls = type(entity_cls.__name__ + 'Model', (SqlalchemyModel, ), attrs)

            self._model_classes[entity_cls.meta_.schema_name] = model_cls

        # Set Entity Class as a class level attribute for the Model, to be able to reference later.
        return model_cls

    def get_repository(self, entity_cls):
        """ Return a repository object configured with a live connection"""
        return SARepository(self, entity_cls, self.get_model(entity_cls))

    def raw(self, query: Any, data: Any = None):
        """Run raw query on Provider"""
        if data is None:
            data = {}
        assert isinstance(query, str)
        assert isinstance(data, (dict, None))

        return self.get_connection().execute(query, data)


operators = {
    'exact': '__eq__',
    'iexact': 'ilike',
    'contains': 'contains',
    'icontains': 'ilike',
    'startswith': 'startswith',
    'endswith': 'endswith',
    'gt': '__gt__',
    'gte': '__ge__',
    'lt': '__lt__',
    'lte': '__le__',
    'in': 'in_',
    'overlap': 'overlap',
    'any': 'any',
}


class DefaultLookup(BaseLookup):
    """Base class with default implementation of expression construction"""

    def __init__(self, source, target, model_cls):
        """Source is LHS and Target is RHS of a comparsion"""
        self.model_cls = model_cls
        super().__init__(source, target)

    def process_source(self):
        """Return source with transformations, if any"""
        source_col = getattr(self.model_cls, self.source)
        return source_col

    def process_target(self):
        """Return target with transformations, if any"""
        return self.target

    def as_expression(self):
        lookup_func = getattr(self.process_source(),
                              operators[self.lookup_name])
        return lookup_func(self.process_target())


@SAProvider.register_lookup
class Exact(DefaultLookup):
    """Exact Match Query"""
    lookup_name = 'exact'


@SAProvider.register_lookup
class IExact(DefaultLookup):
    """Exact Case-Insensitive Match Query"""
    lookup_name = 'iexact'


@SAProvider.register_lookup
class Contains(DefaultLookup):
    """Exact Contains Query"""
    lookup_name = 'contains'


@SAProvider.register_lookup
class IContains(DefaultLookup):
    """Exact Case-Insensitive Contains Query"""
    lookup_name = 'icontains'

    def process_target(self):
        """Return target in lowercase"""
        assert isinstance(self.target, str)
        return f"%{super().process_target()}%"


@SAProvider.register_lookup
class Startswith(DefaultLookup):
    """Exact Contains Query"""
    lookup_name = 'startswith'


@SAProvider.register_lookup
class Endswith(DefaultLookup):
    """Exact Contains Query"""
    lookup_name = 'endswith'


@SAProvider.register_lookup
class GreaterThan(DefaultLookup):
    """Greater than Query"""
    lookup_name = 'gt'


@SAProvider.register_lookup
class GreaterThanOrEqual(DefaultLookup):
    """Greater than or Equal Query"""
    lookup_name = 'gte'


@SAProvider.register_lookup
class LessThan(DefaultLookup):
    """Less than Query"""
    lookup_name = 'lt'


@SAProvider.register_lookup
class LessThanOrEqual(DefaultLookup):
    """Less than or Equal Query"""
    lookup_name = 'lte'


@SAProvider.register_lookup
class In(DefaultLookup):
    """In Query"""
    lookup_name = 'in'

    def process_target(self):
        """Ensure target is a list or tuple"""
        assert isinstance(self.target, (list, tuple))
        return super().process_target()


@SAProvider.register_lookup
class Overlap(DefaultLookup):
    """In Query"""
    lookup_name = 'in'

    def process_target(self):
        """Ensure target is a list or tuple"""
        assert isinstance(self.target, (list, tuple))
        return super().process_target()


@SAProvider.register_lookup
class Any(DefaultLookup):
    """In Query"""
    lookup_name = 'in'

    def process_target(self):
        """Ensure target is a list or tuple"""
        assert isinstance(self.target, (list, tuple))
        return super().process_target()
