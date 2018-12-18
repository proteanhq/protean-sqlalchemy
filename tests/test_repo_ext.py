"""Module to test Repository extended functionality """
from datetime import datetime

from protean.core import field
from protean.core.entity import Entity
from protean.core.repository import repo

from protean_sqlalchemy.repository import SqlalchemySchema

from .test_repository import DogSchema


class Human(Entity):
    """This is a dummy Dog Entity class"""
    name = field.StringMedium(required=True, unique=True)
    age = field.Integer()
    weight = field.Float()
    is_married = field.Boolean(default=True)
    date_of_birth = field.Date(required=True)
    hobbies = field.List()
    profile = field.Dict()
    address = field.Text()
    created_at = field.DateTime(default=datetime.utcnow)

    def __repr__(self):
        return f'<Human id={self.id}>'


class HumanSchema(SqlalchemySchema):
    """ Schema for the Human Entity"""

    class Meta:
        """ Meta class for schema options"""
        entity = Human
        schema_name = 'humans'
        bind = 'another_db'


class TestSqlalchemyRepositoryExt:
    """Class to test Sqlalchemy Repository"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        repo.register(HumanSchema)
        repo.register(DogSchema)

        # Create all the tables
        for conn in repo.connections.values():
            SqlalchemySchema.metadata.create_all(conn.bind)

    def test_create(self):
        """ Test creating an entity with all field types"""

        # Create the entity and validate the results
        human = repo.HumanSchema.create(
            name='John Doe', age='30', weight='13.45',
            date_of_birth='01-01-2000',
            hobbies=['swimming'],
            address='Address of the home of John Doe',
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
            'address': 'Address of the home of John Doe',
            'date_of_birth': datetime(2000, 1, 1).date(),
            'created_at': human.created_at

        }
        assert human.to_dict() == expected

        # Check if the object is in the repo
        human = repo.HumanSchema.get(1)
        assert human is not None
        assert human.to_dict() == expected

    def test_multiple_dbs(self):
        """ Test repository connections to multiple databases"""
        humans = repo.HumanSchema.filter()
        assert humans is not None

        dogs = repo.DogSchema.filter()
        assert dogs is not None
