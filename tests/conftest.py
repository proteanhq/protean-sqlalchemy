"""Module to setup Factories and other required artifacts for tests"""
import os

import pytest

os.environ['PROTEAN_CONFIG'] = 'tests.support.sample_config'


@pytest.fixture(scope="session", autouse=True)
def register_models():
    """Register Test Models with Dict Repo

       Run only once for the entire test suite
    """
    from protean.core.repository import repo_factory
    from protean.core.provider import providers

    from tests.support.dog import Dog, RelatedDog
    from tests.support.human import Human, RelatedHuman

    repo_factory.register(Dog)
    repo_factory.register(RelatedDog)
    repo_factory.register(Human)
    repo_factory.register(RelatedHuman)

    for entity_name in repo_factory._registry:
        repo_factory.get_repository(repo_factory._registry[entity_name].entity_cls)

    # Now, create all associated tables
    for _, provider in providers._providers.items():
        provider._metadata.create_all()

    yield

    # Drop all tables at the end of test suite
    for _, provider in providers._providers.items():
        provider._metadata.drop_all()

@pytest.fixture(autouse=True)
def run_around_tests():
    """Truncate data after each test run"""
    from protean.core.repository import repo_factory

    from tests.support.dog import Dog, RelatedDog
    from tests.support.human import Human, RelatedHuman

    # A test function will be run at this point
    yield

    # Truncate tables
    #   FIXME We are deleting records here, but TRUNCATE is typically much faster
    repo_factory.get_repository(Dog).delete_all()
    repo_factory.get_repository(RelatedDog).delete_all()
    repo_factory.get_repository(Human).delete_all()
    repo_factory.get_repository(RelatedHuman).delete_all()
