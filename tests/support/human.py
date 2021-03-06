""" Define entities of the Human Type """
from datetime import datetime

from protean.core import field
from protean.core.entity import Entity
from protean.core.field import association


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

    class Meta:
        provider = 'another_db'


class RelatedHuman(Entity):
    """This is a dummy Dog Entity class"""
    name = field.StringMedium(required=True, unique=True)
    age = field.Integer()
    weight = field.Float()
    date_of_birth = field.Date(required=True)
    dogs = association.HasMany('RelatedDog', via='owner_id')

    def __repr__(self):
        return f'<RelatedHuman id={self.id}>'
