"""This module holds the definition of Database connectivity"""

from sqlalchemy import orm
from sqlalchemy import create_engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.declarative import as_declarative, declared_attr

from protean.core.repository import BaseConnectionHandler, BaseSchema, \
    BaseRepository, Pagination
from protean.core.exceptions import ConfigurationError

from .sa import DeclarativeMeta


class ConnectionHandler(BaseConnectionHandler):
    """Manage connections to the Sqlalchemy ORM"""

    def __init__(self, conn_info: dict):
        if not conn_info.get('DATABASE_URI'):
            raise ConfigurationError(
                '`DATABASE_URI` setting must be defined for the repository.')
        self.conn_info = conn_info

    def get_connection(self):
        """ Create the connection to the Database instance"""
        # First create the engine
        engine = create_engine(make_url(self.conn_info['DATABASE_URI']))

        # Create the session
        session_cls = orm.sessionmaker(bind=engine)

        return session_cls()


@as_declarative(metaclass=DeclarativeMeta)
class SqlalchemySchema(BaseSchema):
    """Schema representation for the Sqlalchemy Database """

    @declared_attr
    def __tablename__(cls):
        return cls.opts_.schema_name

    @classmethod
    def from_entity(cls, entity):
        """ Convert the entity to a schema object """
        return cls(**entity.to_dict())

    @classmethod
    def to_entity(cls, schema_obj):
        """ Convert the schema object to an entity """
        item_dict = {}
        for field_name in cls.opts_.entity_cls.meta_.declared_fields:
            item_dict[field_name] = getattr(schema_obj, field_name, None)
        return cls.opts_.entity_cls(item_dict)


class Repository(BaseRepository):
    """Repository implementation for the Elasticsearch Database"""

    def _filter_objects(self, page: int = 1, per_page: int = 10,
                        order_by: list = (), excludes_: dict = None,
                        **filters) -> Pagination:
        """ Filter objects from the sqlalchemy database """
        qs = self.conn.query(self.schema_cls)

        # apply the rest of the filters and excludes
        for fk, fv in filters.items():
            col = getattr(self.schema_cls, fk)
            if type(fv) in (list, tuple):
                qs = qs.filter(col.in_(fv))
            else:
                qs = qs.filter(col == fv)

        for ek, ev in excludes_.items():
            col = getattr(self.schema_cls, ek)
            if type(ev) in (list, tuple):
                qs = qs.filter(~col.in_(ev))
            else:
                qs = qs.filter(col != ev)

        # apply the ordering
        order_cols = []
        for order_col in order_by:
            col = getattr(self.schema_cls, order_col.lstrip('-'))
            if order_col.startswith('-'):
                order_cols.append(col.desc())
            else:
                order_cols.append(col)
        qs.order_by(*order_cols)

        # apply limit and offset filters only if per_page is not None
        if per_page is not None:
            offset = (page - 1) * per_page
            qs = qs.limit(per_page).offset(offset)

        # Return the results
        result = Pagination(
            page=page,
            per_page=per_page,
            total=qs.count(),
            items=qs.all())
        return result

    def _create_object(self, schema_obj):
        """ Add a new record to the sqlalchemy database"""
        self.conn.add(schema_obj)

        # If the schema has Auto fields then flush to get them
        if self.entity_cls.meta_.has_auto_field:
            self.conn.flush()
        self.conn.commit()

        return schema_obj

    def _update_object(self, schema_obj):
        """ Update a record in the sqlalchemy database"""
        primary_key, data = {}, {}
        for field_name, field_obj in \
                self.entity_cls.meta_.declared_fields.items():
            if field_obj.identifier:
                primary_key = {
                    field_name: getattr(schema_obj, field_name)
                }
            else:
                data[field_name] = getattr(schema_obj, field_name, None)

        # Run the update query and commit the results
        self.conn.query(self.schema_cls).filter_by(
            **primary_key).update(data)
        self.conn.commit()

        return schema_obj

    def _delete_objects(self, **filters):
        """ Delete a record from the sqlalchemy database"""
        qs = self.conn.query(self.schema_cls)
        return qs.filter_by(**filters).delete()
