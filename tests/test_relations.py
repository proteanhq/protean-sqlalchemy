"""Module to test Repository extended functionality """
from protean.core.repository import repo_factory

from protean_sqlalchemy.utils import create_tables
from protean_sqlalchemy.utils import drop_tables

from .support.dog import RelatedDog
from .support.dog import RelatedDogModel
from .support.human import RelatedHuman
from .support.human import RelatedHumanModel


class TestRelations:
    """Class to test Relation field of Sqlalchemy Repository"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        repo_factory.register(RelatedHumanModel)
        repo_factory.register(RelatedDogModel)

        # Save the current connection
        cls.conn = repo_factory.connections['default']

        # Create all the tables
        create_tables()

        # Create the Humans for filtering
        cls.h1 = RelatedHuman.create(
            name='John Doe', age='30', weight='13.45',
            date_of_birth='01-01-1989')
        cls.h2 = RelatedHuman.create(
            name='Greg Manning', age='44', weight='23.45',
            date_of_birth='30-07-1975')

    @classmethod
    def teardown_class(cls):
        # Drop all the tables
        drop_tables()

    def test_create_related(self):
        """Test Cceating an entity with a related field"""
        dog = RelatedDog(name='Jimmy', age=10, owner=self.h1)
        dog.save()

        assert dog is not None
        assert dog.owner.name == 'John Doe'

        # Check if the object is in the repo
        dog_db = self.conn.query(RelatedDogModel).get(dog.id)
        assert dog_db is not None
        assert dog_db.owner_id == self.h1.id

    def test_update_related(self):
        """ Test updating the related field of an entity """
        dog = RelatedDog.query.filter(name='Jimmy').all().first
        dog.update(owner=self.h2)

        # Check if the object is in the repo
        dog_db = self.conn.query(RelatedDogModel).get(dog.id)
        assert dog_db is not None
        assert dog_db.owner_id == self.h2.id

    def test_has_many(self):
        """ Test getting the has many attribute of Relation"""
        # Get the dogs related to the human
        assert self.h1.dogs is None

        # Create some dogs
        RelatedDog.create(name='Dex', age=6, owner=self.h1)
        RelatedDog.create(name='Lord', age=3, owner=self.h1)

        # Get the dogs related to the human
        assert self.h1.dogs is not None
        assert [d.name for d in self.h1.dogs] == ['Dex', 'Lord']
