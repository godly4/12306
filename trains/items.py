# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field

class TrainsItem(Item):
    # define the fields for your item here like:
    _id = Field()
    name = Field()
    ch_name = Field()
    train_num = Field()
    train_info = Field()