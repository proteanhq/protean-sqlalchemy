"""Module to test Repository extended functionality """
from datetime import datetime

from protean.core.repository import repo_factory
from protean.utils.query import Q

from protean_sqlalchemy.repository import SqlalchemyModel
from protean_sqlalchemy.utils import drop_tables

from .support.human import Human
from .support.human import HumanModel


class TestFiltersLookups:
    """Class to test Sqlalchemy Repository"""

    @classmethod
    def setup_class(cls):
        """ Setup actions for this test case"""
        repo_factory.register(HumanModel)

        # Create all the tables
        for conn in repo_factory.connections.values():
            SqlalchemyModel.metadata.create_all(conn.bind)

        # Create the Humans for filtering
        cls.humans = [
            Human.create(name='John Doe', age='30', weight='13.45',
                         date_of_birth='01-01-1989'),
            Human.create(name='Jane Doe', age='25', weight='17.45',
                         date_of_birth='23-08-1994'),
            Human.create(name='Greg Manning', age='44', weight='23.45',
                         date_of_birth='30-07-1975'),
            Human.create(name='Red Dread', age='23', weight='33.45',
                         date_of_birth='12-03-1996')
        ]

    @classmethod
    def teardown_class(cls):
        # Drop all the tables
        drop_tables()

    def test_iexact_lookup(self):
        """ Test the iexact lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(name__iexact='John doe')

        assert humans is not None
        assert humans.total == 1

    def test_contains_lookup(self):
        """ Test the contains lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(name__contains='Doe')

        assert humans is not None
        assert humans.total == 2

    def test_icontains_lookup(self):
        """ Test the icontains lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(name__icontains='man')

        assert humans is not None
        assert humans.total == 1
        assert humans[0].id == self.humans[2].id

    def test_startswith_lookup(self):
        """ Test the startswith lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(name__startswith='John')

        assert humans is not None
        assert humans.total == 1
        assert humans[0].id == self.humans[0].id

    def test_endswith_lookup(self):
        """ Test the endswith lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(name__endswith='Doe')

        assert humans is not None
        assert humans.total == 2
        assert humans[0].id == self.humans[0].id

    def test_gt_lookup(self):
        """ Test the gt lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(age__gt=40)

        assert humans is not None
        assert humans.total == 1
        assert humans[0].id == self.humans[2].id

    def test_gte_lookup(self):
        """ Test the gte lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(age__gte=30).order_by(['age'])

        assert humans is not None
        assert humans.total == 2
        assert humans[0].id == self.humans[0].id

    def test_lt_lookup(self):
        """ Test the lt lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(weight__lt=15)

        assert humans is not None
        assert humans.total == 1
        assert humans[0].id == self.humans[0].id

    def test_lte_lookup(self):
        """ Test the lte lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(weight__lte=23.45)

        assert humans is not None
        assert humans.total == 3
        assert humans[0].id == self.humans[0].id

    def test_in_lookup(self):
        """ Test the lte lookup of the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(id__in=[self.humans[1].id,
                                            self.humans[3].id])
        assert humans is not None
        assert humans.total == 2
        assert humans[0].id == self.humans[1].id

    def test_date_lookup(self):
        """ Test the lookup of date fields for the Adapter """

        # Filter the entity and validate the results
        humans = Human.query.filter(
            date_of_birth__gt='1994-01-01')

        assert humans is not None
        assert humans.total == 2
        assert humans[0].id == self.humans[1].id

        humans = Human.query.filter(
            date_of_birth__lte=datetime(1989, 1, 1).date())

        assert humans is not None
        assert humans.total == 2
        assert humans[0].id == self.humans[0].id

    def test_q_filters(self):
        """ Test that complex filtering using the Q object"""

        # Filter by 2 conditions
        humans = Human.query.filter(Q(name__contains='Doe') & Q(age__gt=28))
        assert humans is not None
        assert humans.total == 1
        assert humans[0].id == self.humans[0].id

        # Try the same with negation
        humans = Human.query.filter(~Q(name__contains='Doe') & Q(age__gt=28))
        assert humans is not None
        assert humans.total == 1
        assert humans[0].id == self.humans[2].id

        # Try with basic or
        humans = Human.query.filter(Q(name__contains='Doe') | Q(age__gt=28))
        assert humans is not None
        assert humans.total == 3
        assert humans[0].id == self.humans[0].id

        # Try combination of and and or
        humans = Human.query.filter(Q(age__gte=27) | Q(weight__gt=15),
                                    name__contains='Doe')
        assert humans is not None
        assert humans.total == 2
        assert humans[0].id == self.humans[0].id

        # Try combination of and and or
        humans = Human.query.filter(
            (Q(weight__lte=20) | (Q(age__gt=30) & Q(name__endswith='Manning'))),
            Q(date_of_birth__gt='1994-01-01'))
        assert humans is not None
        assert humans.total == 1
        assert humans[0].id == self.humans[1].id
