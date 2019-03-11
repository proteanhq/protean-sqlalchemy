""" Define entities of the Human Type """
from protean.core import field
from protean.core.entity import Entity

from protean_sqlalchemy.repository import SqlalchemyModel


class Dog(Entity):
    """This is a dummy Dog Entity class"""
    name = field.String(required=True, max_length=50, unique=True)
    owner = field.String(required=True, max_length=15)
    age = field.Integer(default=5)

    def __repr__(self):
        return f'<Dog id={self.id}>'


class DogModel(SqlalchemyModel):
    """Model for the Dog Entity"""

    class Meta:
        """ Meta class for model options"""
        entity = Dog
        model_name = 'dogs'


class RelatedDog(Entity):
    """This is a dummy Dog Entity class"""
    name = field.String(required=True, max_length=50, unique=True)
    owner = field.Reference('RelatedHuman')
    age = field.Integer(default=5)

    def __repr__(self):
        return f'<RelatedDog id={self.id}>'


class RelatedDogModel(SqlalchemyModel):
    """Model for the Dog Entity"""

    class Meta:
        """ Meta class for model options"""
        entity = RelatedDog
        model_name = 'related_dogs'
