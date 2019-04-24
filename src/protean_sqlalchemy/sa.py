""" Module for defining overriding functions of sqlalchemy

    isort:skip_file
"""
from abc import ABCMeta

from protean.core import field
from protean.core.repository import repo_factory

from sqlalchemy import types as sa_types, Column
from sqlalchemy.ext import declarative as sa_dec


class DeclarativeMeta(sa_dec.DeclarativeMeta, ABCMeta):
    """ Metaclass for the Sqlalchemy declarative schema """
    field_mapping = {
        field.Auto: sa_types.Integer,
        field.String: sa_types.String,
        field.Text: sa_types.Text,
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
        if hasattr(cls, 'entity_cls'):
            entity_cls = cls.entity_cls
            for field_name, field_obj in entity_cls.meta_.declared_fields.items():

                # Map the field if not in attributes
                if field_name not in cls.__dict__:
                    field_cls = type(field_obj)
                    if field_cls == field.Reference:
                        related_ent = repo_factory.get_entity(field_obj.to_cls.__name__)
                        if field_obj.via:
                            related_attr = getattr(
                                related_ent, field_obj.via)
                        else:
                            related_attr = related_ent.meta_.id_field
                        field_name = field_obj.get_attribute_name()
                        field_cls = type(related_attr)

                    # Get the SA type and default to the text type if no
                    # mapping is found
                    sa_type_cls = cls.field_mapping.get(field_cls)
                    if not sa_type_cls:
                        sa_type_cls = sa_types.String

                    # Build the column arguments
                    col_args = {
                        'primary_key': field_obj.identifier,
                        'nullable': not field_obj.required,
                        'unique': field_obj.unique
                    }

                    # Update the arguments based on the field type
                    type_args = {}
                    if issubclass(field_cls, field.String):
                        type_args['length'] = field_obj.max_length

                    # Update the attributes of the class
                    setattr(cls, field_name,
                            Column(sa_type_cls(**type_args), **col_args))
        super().__init__(classname, bases, dict_)
