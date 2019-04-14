"""Module to test Provider Class"""
from datetime import datetime

from protean.conf import active_config
from sqlalchemy.engine import ResultProxy

from protean_sqlalchemy.provider import SAProvider

from .support.dog import Dog
from .support.dog import RelatedDog
from .support.human import RelatedHuman


class TestSAProvider:
    """Class to test Connection Handler class"""

    @classmethod
    def setup_class(cls):
        """Setup actions for this test case"""
        cls.repo_conf = active_config.DATABASES['default']

    def test_init(self):
        """Test Initialization of Sqlalchemy DB"""
        provider = SAProvider(self.repo_conf)
        assert provider is not None

    def test_connection(self):
        """Test the connection to the repository"""
        provider = SAProvider(self.repo_conf)
        conn = provider.get_connection()
        assert conn is not None

        # Execute a simple query to test the connection
        resp = conn.execute(
            'SELECT * FROM sqlite_master WHERE type="table"')
        assert len(list(resp)) > 1

    def test_raw(self):
        """Test raw queries on Provider"""
        Dog.create(name='Cash', owner='John', age=10)
        Dog.create(name='Boxy', owner='Carry', age=4)
        Dog.create(name='Gooey', owner='John', age=2)

        john = RelatedHuman.create(name='John Doe', age=26,
                                   date_of_birth=datetime(1993, 1, 1).date())
        RelatedDog.create(name='Rubble', age=4, owner=john)

        provider = SAProvider(self.repo_conf)
        result = provider.raw('SELECT * FROM dog')
        assert result is not None
        assert isinstance(result, ResultProxy)
        assert len(list(result)) == 3

        result = provider.raw('SELECT * FROM dog WHERE owner="John"')
        assert len(list(result)) == 2

        # With a Join query, which is the whole point of this raw method
        result = provider.raw('SELECT dog.name, dog.age, human.name, human.age '
                              'FROM related_dog dog INNER JOIN related_human human '
                              'ON dog.owner_id = human.id')
        assert len(list(result)) == 1

        result = provider.raw('SELECT dog.name, dog.age, human.name, human.age '
                              'FROM related_dog dog INNER JOIN related_human human '
                              'ON dog.owner_id = human.id '
                              'WHERE dog.age = :dog_age',
                              {'dog_age': 4}
                              )
        assert len(list(result)) == 1
