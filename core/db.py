# -*- coding: UTF-8 -*-
import pymongo
from core.config import config

class DBClient(pymongo.MongoClient):
    def __init__(
        self,
        host: str = config.MongoDBURI,
    ) -> None:
        super().__init__(
            host=host
        )

