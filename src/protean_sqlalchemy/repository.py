"""This module holds the definition of Database connectivity"""

from protean.core import field
from protean.core.exceptions import ConfigurationError
from protean.core.repository import BaseAdapter
from protean.core.repository import BaseConnectionHandler
from protean.core.repository import BaseModel
from protean.core.repository import Lookup
from protean.core.repository import Pagination
from protean.utils.query import Q
from sqlalchemy import and_
from sqlalchemy import create_engine
from sqlalchemy import or_
from sqlalchemy import orm
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.declarative import declared_attr

from .sa import DeclarativeMeta


class ConnectionHandler(BaseConnectionHandler):
    """Manage connections to the Sqlalchemy ORM"""

    def __init__(self, conn_name: str, conn_info: dict):
        self. conn_name = conn_name
        if not conn_info.get('DATABASE_URI'):
            raise ConfigurationError(
                '`DATABASE_URI` setting must be defined for the repository.')
        self.conn_info = conn_info

    def get_connection(self):
        """ Create the connection to the Database instance"""
        # First create the engine
        engine = create_engine(make_url(self.conn_info['DATABASE_URI']))

        # Create the session
        session_factory = orm.sessionmaker(bind=engine)
        session_cls = orm.scoped_session(session_factory)

        return session_cls()

    def close_connection(self, conn):
        """ Close the connection to the Database instance """
        conn.close()


@as_declarative(metaclass=DeclarativeMeta)
class SqlalchemyModel(BaseModel):
    """Model representation for the Sqlalchemy Database """

    @declared_attr
    def __tablename__(cls):
        return cls.opts_.model_name

    @classmethod
    def from_entity(cls, entity):
        """ Convert the entity to a model object """
        item_dict = {}
        for field_obj in cls.opts_.entity_cls.declared_fields.values():
            if isinstance(field_obj, field.Reference):
                item_dict[field_obj.relation.field_name] = \
                    field_obj.relation.value
            else:
                item_dict[field_obj.field_name] = getattr(
                    entity, field_obj.field_name)
        return cls(**item_dict)

    @classmethod
    def to_entity(cls, model_obj):
        """ Convert the model object to an entity """
        item_dict = {}
        for field_name in cls.opts_.entity_cls.declared_fields:
            item_dict[field_name] = getattr(model_obj, field_name, None)
        return cls.opts_.entity_cls(item_dict)


class Adapter(BaseAdapter):
    """Adapter implementation for the Databases compliant with SQLAlchemy"""

    def _build_filters(self, criteria: Q):
        """ Recursively Build the filters from the criteria object"""
        # Decide the function based on the connector type
        func = and_ if criteria.connector == criteria.AND else or_
        params = []
        for child in criteria.children:
            if isinstance(child, Q):
                # Call the function again with the child
                params.append(self._build_filters(child))
            else:
                # Find the lookup class and the key
                stripped_key, lookup_class = self._extract_lookup(child[0])

                # Instantiate the lookup class and get the expression
                lookup = lookup_class(stripped_key, child[1], self.model_cls)
                if criteria.negated:
                    params.append(~lookup.as_expression())
                else:
                    params.append(lookup.as_expression())

        return func(*params)

    def _filter_objects(self, criteria: Q, page: int = 1, per_page: int = 10,
                        order_by: list = ()) -> Pagination:
        """ Filter objects from the sqlalchemy database """
        qs = self.conn.query(self.model_cls)

        # Build the filters from the criteria
        if criteria.children:
            qs = qs.filter(self._build_filters(criteria))

        # Apply the order by clause if present
        order_cols = []
        for order_col in order_by:
            col = getattr(self.model_cls, order_col.lstrip('-'))
            if order_col.startswith('-'):
                order_cols.append(col.desc())
            else:
                order_cols.append(col)
        qs = qs.order_by(*order_cols)

        # apply limit and offset filters only if per_page is not None
        if per_page > 0:
            offset = (page - 1) * per_page
            qs = qs.limit(per_page).offset(offset)

        # Return the results
        try:
            items = qs.all()
            total = qs.count() if per_page > 0 else len(items)
            result = Pagination(
                page=page,
                per_page=per_page,
                total=total,
                items=items)
        except DatabaseError:
            self.conn.rollback()
            raise

        return result

    def _create_object(self, model_obj):
        """ Add a new record to the sqlalchemy database"""
        self.conn.add(model_obj)

        try:
            # If the model has Auto fields then flush to get them
            if self.entity_cls.auto_fields:
                self.conn.flush()
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise

        return model_obj

    def _update_object(self, model_obj):
        """ Update a record in the sqlalchemy database"""
        primary_key, data = {}, {}
        for field_name, field_obj in \
                self.entity_cls.declared_fields.items():
            if field_obj.identifier:
                primary_key = {
                    field_name: getattr(model_obj, field_name)
                }
            else:
                if isinstance(field_obj, field.Reference):
                    data[field_obj.relation.field_name] = \
                        field_obj.relation.value
                else:
                    data[field_name] = getattr(model_obj, field_name, None)

        # Run the update query and commit the results
        try:
            self.conn.query(self.model_cls).filter_by(
                **primary_key).update(data)
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise

        return model_obj

    def _delete_objects(self, **filters):
        """ Delete a record from the sqlalchemy database"""
        # Delete the objects and commit the results
        qs = self.conn.query(self.model_cls)
        try:
            del_count = qs.filter_by(**filters).delete()
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise
        return del_count


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


class DefaultLookup(Lookup):
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


@Adapter.register_lookup
class Exact(DefaultLookup):
    """Exact Match Query"""
    lookup_name = 'exact'


@Adapter.register_lookup
class IExact(DefaultLookup):
    """Exact Case-Insensitive Match Query"""
    lookup_name = 'iexact'


@Adapter.register_lookup
class Contains(DefaultLookup):
    """Exact Contains Query"""
    lookup_name = 'contains'


@Adapter.register_lookup
class IContains(DefaultLookup):
    """Exact Case-Insensitive Contains Query"""
    lookup_name = 'icontains'

    def process_target(self):
        """Return target in lowercase"""
        assert isinstance(self.target, str)
        return f"%{super().process_target()}%"


@Adapter.register_lookup
class Startswith(DefaultLookup):
    """Exact Contains Query"""
    lookup_name = 'startswith'


@Adapter.register_lookup
class Endswith(DefaultLookup):
    """Exact Contains Query"""
    lookup_name = 'endswith'


@Adapter.register_lookup
class GreaterThan(DefaultLookup):
    """Greater than Query"""
    lookup_name = 'gt'


@Adapter.register_lookup
class GreaterThanOrEqual(DefaultLookup):
    """Greater than or Equal Query"""
    lookup_name = 'gte'


@Adapter.register_lookup
class LessThan(DefaultLookup):
    """Less than Query"""
    lookup_name = 'lt'


@Adapter.register_lookup
class LessThanOrEqual(DefaultLookup):
    """Less than or Equal Query"""
    lookup_name = 'lte'


@Adapter.register_lookup
class In(DefaultLookup):
    """In Query"""
    lookup_name = 'in'

    def process_target(self):
        """Ensure target is a list or tuple"""
        assert type(self.target) in (list, tuple)
        return super().process_target()


@Adapter.register_lookup
class Overlap(DefaultLookup):
    """In Query"""
    lookup_name = 'in'

    def process_target(self):
        """Ensure target is a list or tuple"""
        assert type(self.target) in (list, tuple)
        return super().process_target()


@Adapter.register_lookup
class Any(DefaultLookup):
    """In Query"""
    lookup_name = 'in'

    def process_target(self):
        """Ensure target is a list or tuple"""
        assert type(self.target) in (list, tuple)
        return super().process_target()
