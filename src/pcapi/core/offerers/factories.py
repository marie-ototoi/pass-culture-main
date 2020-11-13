import uuid

import factory

from pcapi import models
from pcapi.core.testing import BaseFactory


class ProviderFactory(BaseFactory):
    class Meta:
        model = models.Provider
        sqlalchemy_get_or_create = ["localClass"]

    name = factory.Sequence("Provider {}".format)
    localClass = None
    apiKey = factory.LazyFunction(lambda: str(uuid.uuid4()).replace("-", ""))
