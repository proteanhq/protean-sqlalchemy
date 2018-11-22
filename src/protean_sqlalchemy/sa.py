""" Module for defining overriding functions of sqlalchemy """

from sqlalchemy.ext import declarative as sa_dec
from sqlalchemy import types as sa_types, Column

from protean.core import field
from protean.utils.meta import OptionsMeta


class DeclarativeMeta(sa_dec.DeclarativeMeta, OptionsMeta):
    """ Metaclass for the Sqlalchemy declarative schema """
    field_mapping = {
        field.Auto: sa_types.Integer,
        field.String: sa_types.String,
        field.Boolean: sa_types.Boolean,
        field.Integer: sa_types.Integer,
        field.Float: sa_types.Float,
        field.List: sa_types.PickleType,
        field.Dict: sa_types.PickleType,
        field.Date: sa_types.Date,
        field.DateTime: sa_types.DateTime,
    }

    def __init__(cls, classname, bases, dict_):
        # Update the class attrs with the entity attributes
        if cls.__dict__.get('opts_'):
            entity_cls = cls.__dict__['opts_'].entity_cls
            for field_name, field_obj in entity_cls.meta_.\
                    declared_fields.items():

                # Map the field if not in attributes
                if field_name not in cls.__dict__:
                    field_cls = type(field_obj)
                    sa_type_cls = cls.field_mapping.get(field_cls)

                    # Build the column arguments
                    col_args = {
                        'primary_key': field_obj.identifier,
                        'nullable': not field_obj.required,
                        'unique': field_obj.unique
                    }

                    # Update the attributes of the class
                    setattr(cls, field_name, Column(sa_type_cls, **col_args))

        super().__init__(classname, bases, dict_)