import random
import string
from factory import Sequence, post_generation, LazyAttribute, Faker
from factory.alchemy import SQLAlchemyModelFactory
from factory.fuzzy import FuzzyFloat, FuzzyInteger, FuzzyText, FuzzyChoice

from db import models
from label import load_labels, label_names_by_type, label_types_by_region
from . import database

load_labels()


def random_label_name_by_label_type_and_region(label_type: str, region: str):
    if label_type in label_types_by_region(region):
        return random.choice(label_names_by_type(label_type))
    else:
        return None


class BaseFactory(SQLAlchemyModelFactory):
    class Meta:
        abstract = True
        sqlalchemy_session = database.Session
        sqlalchemy_session_persistence = "commit"


class FileFactory(BaseFactory):
    class Meta:
        model = models.File

    id = Sequence(lambda n: n)
    name = Sequence(lambda n: f'File {n}')
    size = FuzzyInteger(1, 100)


class ImageFactory(BaseFactory):
    class Meta:
        model = models.Image

    id = Sequence(lambda n: n)
    hash = FuzzyText(chars=string.hexdigits, length=64)
    width = FuzzyInteger(400, 600)
    height = FuzzyInteger(400, 600)
    url = FuzzyText(prefix='http://', length=10)

    @post_generation
    def file(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.file_id = extracted.id


class BBoxFactory(BaseFactory):
    class Meta:
        model = models.BBox

    id = Sequence(lambda n: n)
    rx1 = FuzzyFloat(0.0, 0.5)
    ry1 = FuzzyFloat(0.0, 0.5)
    rx2 = FuzzyFloat(0.5, 1.0)
    ry2 = FuzzyFloat(0.5, 1.0)

    @post_generation
    def image(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.image_id = extracted.id

    @post_generation
    def label(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.label = extracted


class LabelFactory(BaseFactory):
    class Meta:
        model = models.Label

    id = Sequence(lambda n: n)
    region = FuzzyChoice(label_names_by_type('region'))
    style = LazyAttribute(lambda o: random_label_name_by_label_type_and_region(label_type='style', region=o.region))
    category = LazyAttribute(lambda o: random_label_name_by_label_type_and_region(label_type='category', region=o.region))
    fabric = LazyAttribute(lambda o: random_label_name_by_label_type_and_region(label_type='fabric', region=o.region))
    unused = Faker('pybool')
    reviewed = Faker('pybool')

    @post_generation
    def bbox(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            self.bbox_id = extracted.id
