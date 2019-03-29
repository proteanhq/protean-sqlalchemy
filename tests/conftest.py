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

    from tests.support.dog import (DogModel, RelatedDogModel)
    from tests.support.human import (HumanModel, RelatedHumanModel)

    repo_factory.register(DogModel)
    repo_factory.register(RelatedDogModel)
    repo_factory.register(HumanModel)
    repo_factory.register(RelatedHumanModel)

    for entity_name in repo_factory._entity_registry:
        getattr(repo_factory, entity_name)

    # Now, create all associated tables
    for _, provider in providers._providers.items():
        provider._metadata.create_all()

    yield

    # Drop all tables at the end of test suite
    for _, provider in providers._providers.items():
        provider._metadata.drop_all()

@pytest.fixture(autouse=True)
def run_around_tests():
    """Initialize DogModel with Dict Repo"""
    from protean.core.repository import repo_factory

    # A test function will be run at this point
    yield

    # Truncate tables
    #   FIXME We are deleting records here, but TRUNCATE is typically much faster
    repo_factory.Dog.delete_all()
    repo_factory.RelatedDog.delete_all()
    repo_factory.Human.delete_all()
    repo_factory.RelatedHuman.delete_all()
