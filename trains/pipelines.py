# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import pymongo
from items import TrainsItem

class TrainsPipeline(object):
    def __init__(self):
        mongoClient = pymongo.MongoClient("localhost", 27017)
        db = mongoClient["train_db"]
        self.Train = db["trains"]

    def process_item(self, item, spider):
        if isinstance(item, TrainsItem):
            self.Train.insert(dict(item))
