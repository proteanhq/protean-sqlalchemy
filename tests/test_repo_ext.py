"""Module to test Repository extended functionality """
import pytest

from datetime import datetime

from protean.core import field
from protean.core.entity import Entity
from protean.core.repository import repo_factory as rf
from protean.core.exceptions import ValidationError
from protean.conf import active_config

from protean_sqlalchemy.repository import SqlalchemySchema


class Human(Entity):
    """This is a dummy Dog Entity class"""
    name = field.String(required=True, max_length=50, unique=True)
    age = field.Integer()
    weight = field.Float()
    is_married = field.Boolean(default=True)
    date_of_birth = field.Date(required=True)
    hobbies = field.List()
    profile = field.Dict()
    created_at = field.DateTime(default=datetime.utcnow)

    def __repr__(self):
        return f'<Human id={self.id}>'


class HumanSchema(SqlalchemySchema):
    """ Schema for the Human Entity"""

    class Meta:
        """ Meta class for schema options"""
        entity = Human
        schema_name = 'humans'


class TestSqlalchemyRepositoryExt:
    """Class to test Sqlalchemy Repository"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        rf.register(HumanSchema)

        # Save the current connection
        cls.conn = rf._connections['default']

        # Create all the tables
        SqlalchemySchema.metadata.create_all(cls.conn.bind)

    def test_create(self):
        """ Test creating an entity with all field types"""

        # Create the entity and validate the results
        human = rf.HumanSchema.create(
            name='John Doe', age='30', weight='13.45',
            date_of_birth='01-01-2000',
            hobbies=['swimming'],
            profile={'phone': '90233143112', 'email': 'johndoe@domain.com'})
        assert human is not None
        expected = {
            'id': 1,
            'name': 'John Doe',
            'weight': 13.45,
            'age': 30,
            'is_married': True,
            'hobbies': ['swimming'],
            'profile': {'email': 'johndoe@domain.com', 'phone': '90233143112'},
            'date_of_birth': datetime(2000, 1, 1).date(),
            'created_at': human.created_at

        }
        assert human.to_dict() == expected

        # Check if the object is in the repo
        human = rf.HumanSchema.get(1)
        assert human is not None
        assert human.to_dict() == expected
