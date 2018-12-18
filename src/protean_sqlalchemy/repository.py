"""This module holds the definition of Database connectivity"""

from protean.core.exceptions import ConfigurationError
from protean.core.repository import BaseConnectionHandler
from protean.core.repository import BaseRepository
from protean.core.repository import BaseSchema
from protean.core.repository import Pagination
from sqlalchemy import create_engine
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

    def _filter_objects(self, page: int = 1, per_page: int = 10,  # noqa: C901
                        order_by: list = (), excludes_: dict = None,
                        **filters) -> Pagination:
        """ Filter objects from the sqlalchemy database """
        qs = self.conn.query(self.schema_cls)

        # check for sqlalchemy filters
        filter_ = filters.pop('filter_', None)
        if filter_ is not None:
            qs = qs.filter(filter_)

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
        qs = qs.order_by(*order_cols)

        # apply limit and offset filters only if per_page is not None
        total = qs.count()
        if per_page > 0:
            offset = (page - 1) * per_page
            qs = qs.limit(per_page).offset(offset)

        # Return the results
        try:
            result = Pagination(
                page=page,
                per_page=per_page,
                total=total,
                items=qs.all())
        except DatabaseError:
            self.conn.rollback()
            raise

        return result

    def _create_object(self, schema_obj):
        """ Add a new record to the sqlalchemy database"""
        self.conn.add(schema_obj)

        try:
            # If the schema has Auto fields then flush to get them
            if self.entity_cls.meta_.has_auto_field:
                self.conn.flush()
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise

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
        try:
            self.conn.query(self.schema_cls).filter_by(
                **primary_key).update(data)
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise

        return schema_obj

    def _delete_objects(self, **filters):
        """ Delete a record from the sqlalchemy database"""
        # Delete the objects and commit the results
        qs = self.conn.query(self.schema_cls)
        try:
            del_count = qs.filter_by(**filters).delete()
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise
        return del_count

    def delete_all(self):
        """ Delete all records in this schema """
        self._delete_objects()
