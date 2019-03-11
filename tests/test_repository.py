"""Module to test Repository Classes and Functionality"""
import pytest
from protean.conf import active_config
from protean.core.exceptions import ValidationError
from protean.core.repository import repo_factory

from protean_sqlalchemy.repository import ConnectionHandler
from protean_sqlalchemy.utils import create_tables
from protean_sqlalchemy.utils import drop_tables

from .support.dog import Dog
from .support.dog import DogModel


class TestConnectionHandler:
    """Class to test Connection Handler class"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        cls.repo_conf = active_config.REPOSITORIES['default']

    def test_init(self):
        """Test Initialization of Sqlalchemy DB"""
        ch = ConnectionHandler('default', self.repo_conf)
        assert ch is not None

    def test_connection(self):
        """ Test the connection to the repository"""
        ch = ConnectionHandler('default', self.repo_conf)
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
        repo_factory.register(DogModel)

        # Save the current connection
        cls.conn = repo_factory.connections['default']

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
        dog = Dog.create(name='Johnny', owner='John')
        assert dog is not None
        assert dog.id == 1
        assert dog.name == 'Johnny'
        assert dog.age == 5

        # Check if the object is in the repo
        dog_db = self.conn.query(DogModel).get(1)
        assert dog_db is not None
        assert dog_db.id == 1
        assert dog_db.name == 'Johnny'

        # Check for unique validation
        with pytest.raises(ValidationError) as e_info:
            Dog.create(name='Johnny', owner='John')
        assert e_info.value.normalized_messages == {
            'name': ['`dogs` with this `name` already exists.']}

    def test_update(self, mocker):
        """ Test updating an entity in the repository"""
        # Update the entity and validate the results
        dog = Dog.get(1)
        dog.update(age=7)
        assert dog is not None
        assert dog.age == 7

        # Check if the object is in the repo
        dog_db = self.conn.query(DogModel).get(1)
        assert dog_db is not None
        assert dog_db.id == 1
        assert dog_db.name == 'Johnny'
        assert dog.age == 7

    def test_filter(self):
        """ Test reading entities from the repository"""
        Dog.create(name='Cash', owner='John', age=10)
        Dog.create(name='Boxy', owner='Carry', age=4)
        Dog.create(name='Gooey', owner='John', age=2)

        # Filter the entity and validate the results
        dogs = Dog.query.filter(owner='John').\
            paginate(page=1, per_page=15).\
            order_by(['-age']).all()

        assert dogs is not None
        assert dogs.total == 3
        dog_ages = [d.age for d in dogs.items]
        assert dog_ages == [10, 7, 2]

        # Test In and not in query
        dogs = Dog.query.filter(name__in=['Cash', 'Boxy'])
        assert dogs.total == 2

        dogs = Dog.query.filter(owner='John').exclude(name__in=['Cash', 'Gooey'])
        assert dogs.total == 1

    def test_delete(self):
        """ Test deleting an entity from the repository"""
        # Delete the entity and validate the results
        dog = Dog.get(1)
        cnt = dog.delete()
        assert cnt == 1

        # Make sure that the entity is deleted
        # Check if the object is in the repo
        dog_db = self.conn.query(DogModel).filter_by(id=1).first()
        assert dog_db is None

    def test_close_connection(self):
        """ Test closing connection to the repository """
        repo_factory.close_connections()
