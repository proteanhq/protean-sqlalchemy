"""Module to test Repository Classes and Functionality"""
import pytest

from protean.core import field
from protean.core.entity import Entity
from protean.core.repository import repo
from protean.core.exceptions import ValidationError
from protean.conf import active_config

from protean_sqlalchemy.repository import SqlalchemySchema, \
    ConnectionHandler
from protean_sqlalchemy.utils import create_tables, drop_tables


class Dog(Entity):
    """This is a dummy Dog Entity class"""
    name = field.String(required=True, max_length=50, unique=True)
    owner = field.String(required=True, max_length=15)
    age = field.Integer(default=5)

    def __repr__(self):
        return f'<Dog id={self.id}>'


class DogSchema(SqlalchemySchema):
    """ Schema for the Dog Entity"""

    class Meta:
        """ Meta class for schema options"""
        entity = Dog
        schema_name = 'dogs'


class TestConnectionHandler:
    """Class to test Connection Handler class"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        cls.repo_conf = active_config.REPOSITORIES['default']

    def test_init(self):
        """Test Initialization of Sqlalchemy DB"""
        ch = ConnectionHandler(self.repo_conf)
        assert ch is not None

    def test_connection(self):
        """ Test the connection to the repository"""
        ch = ConnectionHandler(self.repo_conf)
        conn = ch.get_connection()
        assert conn is not None

        # Execute a simple query to test the connection
        resp = conn.execute(
            'SELECT * FROM sqlite_master WHERE type="table"')
        assert list(resp) == []


class TestSqlalchemyRepository:
    """Class to test Sqlalchemy Repository"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        repo.register(DogSchema)

        # Save the current connection
        cls.conn = repo.connections['default']

        # Create all the tables
        create_tables()

    @classmethod
    def teardown_class(cls):
        """ Teardown actions for this test case"""

        # Drop all the tables
        drop_tables()

    def test_create(self):
        """ Test creating an entity in the repository"""
        # Create the entity and validate the results
        dog = repo.DogSchema.create(name='Johnny', owner='John')
        assert dog is not None
        assert dog.id == 1
        assert dog.name == 'Johnny'
        assert dog.age == 5

        # Check if the object is in the repo
        dog_db = self.conn.query(DogSchema).get(1)
        assert dog_db is not None
        assert dog_db.id == 1
        assert dog_db.name == 'Johnny'

        # Check for unique validation
        with pytest.raises(ValidationError) as e_info:
            repo.DogSchema.create(name='Johnny', owner='John')
        assert e_info.value.normalized_messages == {
            'name': ['`dogs` with this `name` already exists.']}

    def test_update(self, mocker):
        """ Test updating an entity in the repository"""
        # Update the entity and validate the results
        dog = repo.DogSchema.update(identifier=1, data=dict(age=7))
        assert dog is not None
        assert dog.age == 7

        # Check if the object is in the repo
        dog_db = self.conn.query(DogSchema).get(1)
        assert dog_db is not None
        assert dog_db.id == 1
        assert dog_db.name == 'Johnny'
        assert dog.age == 7

    def test_filter(self):
        """ Test reading entities from the repository"""
        repo.DogSchema.create(name='Cash', owner='John', age=10)
        repo.DogSchema.create(name='Boxy', owner='Carry', age=4)
        repo.DogSchema.create(name='Gooey', owner='John', age=2)

        # Filter the entity and validate the results
        dogs = repo.DogSchema.filter(page=1, per_page=15, order_by='-age',
                                     owner='John')
        assert dogs is not None
        assert dogs.total == 3
        assert dogs.items[1].to_dict() == {
            'age': 10, 'id': 2, 'name': 'Cash', 'owner': 'John'}

        # Test In and not in query
        dogs = repo.DogSchema.filter(name=['Cash', 'Boxy'])
        assert dogs.total == 2

        dogs = repo.DogSchema.filter(excludes_=dict(name=['Cash', 'Gooey']),
                                     owner='John')
        assert dogs.total == 1

        # Test for sql alchemy filter
        dogs = repo.DogSchema.filter(filter_=(DogSchema.age > 8))
        assert dogs.total == 1

    def test_delete(self):
        """ Test deleting an entity from the repository"""
        # Delete the entity and validate the results
        cnt = repo.DogSchema.delete(1)
        assert cnt == 1

        # Make sure that the entity is deleted
        # Check if the object is in the repo
        dog_db = self.conn.query(DogSchema).filter_by(id=1).first()
        assert dog_db is None
