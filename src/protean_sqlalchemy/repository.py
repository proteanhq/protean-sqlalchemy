"""This module holds the definition of Database connectivity"""

from typing import Any

from protean.core import field
from protean.core.entity import Entity
from protean.core.repository import BaseModel
from protean.core.repository import BaseRepository
from protean.core.repository import ResultSet
from protean.utils.query import Q
from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.ext.declarative import declared_attr

from .sa import DeclarativeMeta


@as_declarative(metaclass=DeclarativeMeta)
class SqlalchemyModel(BaseModel):
    """Model representation for the Sqlalchemy Database """

    @declared_attr
    def __tablename__(cls):
        return cls.entity_cls.meta_.schema_name

    @classmethod
    def from_entity(cls, entity: Entity):
        """ Convert the entity to a model object """
        item_dict = {}
        for field_obj in cls.entity_cls.meta_.attributes.values():
            if isinstance(field_obj, field.Reference):
                item_dict[field_obj.relation.field_name] = \
                    field_obj.relation.value
            else:
                item_dict[field_obj.field_name] = getattr(
                    entity, field_obj.field_name)
        return cls(**item_dict)

    @classmethod
    def to_entity(cls, model_obj: 'SqlalchemyModel'):
        """ Convert the model object to an entity """
        item_dict = {}
        for field_name in cls.entity_cls.meta_.attributes:
            item_dict[field_name] = getattr(model_obj, field_name, None)
        return cls.entity_cls(item_dict)


class SARepository(BaseRepository):
    """Repository implementation for Databases compliant with SQLAlchemy"""

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
                stripped_key, lookup_class = self.provider._extract_lookup(child[0])

                # Instantiate the lookup class and get the expression
                lookup = lookup_class(stripped_key, child[1], self.model_cls)
                if criteria.negated:
                    params.append(~lookup.as_expression())
                else:
                    params.append(lookup.as_expression())

        return func(*params)

    def filter(self, criteria: Q, offset: int = 0, limit: int = 10,
               order_by: list = ()) -> ResultSet:
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
        qs = qs.limit(limit).offset(offset)

        # Return the results
        try:
            items = qs.all()
            result = ResultSet(
                offset=offset,
                limit=limit,
                total=qs.count(),
                items=items[offset: offset + limit])
        except DatabaseError:
            self.conn.rollback()
            raise

        return result

    def create(self, model_obj):
        """ Add a new record to the sqlalchemy database"""
        self.conn.add(model_obj)

        try:
            # If the model has Auto fields then flush to get them
            if self.entity_cls.meta_.auto_fields:
                self.conn.flush()
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise

        return model_obj

    def update(self, model_obj):
        """ Update a record in the sqlalchemy database"""
        primary_key, data = {}, {}
        for field_name, field_obj in \
                self.entity_cls.meta_.declared_fields.items():
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

    def update_all(self, criteria: Q, *args, **kwargs):
        """ Update all objects satisfying the criteria """
        # Delete the objects and commit the results
        qs = self.conn.query(self.model_cls).filter(self._build_filters(criteria))
        try:
            values = args or {}
            values.update(kwargs)
            updated_count = qs.update(values)
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise
        return updated_count

    def delete(self, model_obj):
        """ Delete the entity record in the dictionary """
        identifier = getattr(model_obj, self.entity_cls.meta_.id_field.field_name)
        primary_key = {self.entity_cls.meta_.id_field.field_name: identifier}
        try:
            self.conn.query(self.model_cls).filter_by(**primary_key).delete()
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise

        return model_obj

    def delete_all(self, criteria: Q = None):
        """ Delete a record from the sqlalchemy database"""
        del_count = 0
        if criteria:
            qs = self.conn.query(self.model_cls).filter(self._build_filters(criteria))
        else:
            qs = self.conn.query(self.model_cls)

        try:
            del_count = qs.delete()
            self.conn.commit()
        except DatabaseError:
            self.conn.rollback()
            raise

        return del_count

    def raw(self, query: Any, data: Any = None):
        """Run a raw query on the repository and return entity objects"""
        assert isinstance(query, str)

        try:
            results = self.conn.execute(query)

            entity_items = []
            for item in results:
                entity = self.model_cls.to_entity(item)
                entity.state_.mark_retrieved()
                entity_items.append(entity)

            result = ResultSet(
                offset=0,
                limit=len(entity_items),
                total=len(entity_items),
                items=entity_items)
        except DatabaseError:
            self.conn.rollback()
            raise

        return result
