# -*- coding: utf-8 -*-

import re
import uuid
import redis
import random
import scrapy
import requests
from scrapy.http import Request
from trains.items import TrainsItem
from scrapy.spiders import CrawlSpider

pool = redis.ConnectionPool(host='localhost', port=6379, db=0)
redisClient = redis.StrictRedis(connection_pool=pool)

def getIp():
    while True:
        count = redisClient.llen("PROXY_IPS")
        index = random.randint(0, count)
        proxyIp = redisClient.lindex("PROXY_IPS", index)
        proxies = {'http': 'http://{0}'.format(proxyIp)}
        try:
            r = requests.get('http://www.baidu.com', timeout=3, proxies=proxies)
            if r.status_code == 200:
                return proxies['http']
        except:
            redisClient.lrem("PROXY_IPS", 0, proxyIp)

#转换时间成分钟格式
def transTime(timeStr):
    timeList = re.findall("\d+", timeStr)
    if len(timeList) == 1:
        return int(timeList[0])
    else:
        return int(timeList[0])*60 + int(timeList[1])

class ProxySpider(CrawlSpider):
    name = "train"
    start_urls = ['https://kyfw.12306.cn/otn/resources/js/framework/station_name.js']
    
    def start_requests(self):
        r = requests.get(self.start_urls[0], verify=False) 
        stations = r.text.split('|')
        index_ch = 1
        index_en = 3
        while index_ch< len(stations):
            TrainItem = TrainsItem()
            chName = stations[index_ch]
            enName = stations[index_en]
            #可能存在汉字拼音不对应的情况
            if chName == u"漯河":
                enName = "leihe"
            TrainItem["ch_name"] = chName
            TrainItem["name"] = enName
            url_station = "http://search.huochepiao.com/chezhan/{0}".format(enName)
            #yield Request(url=url_station, meta={"item": TrainItem, "proxy": getIp()}, callback=self.parseStation)
            yield Request(url=url_station, meta={"item": TrainItem}, callback=self.parseStation)
            index_ch += 5
            index_en += 5

    def parseStation(self, response):
        trains = response.xpath('//a[contains(@href,"checi")]')
        TrainItem = response.meta["item"]
        for train in trains:
            trainNum = train.xpath('b/text()').extract_first()
            url_train = "http://search.huochepiao.com/checi/{0}".format(trainNum)
            #yield Request(url=url_train, meta={"item": TrainItem, "proxy": getIp(), "num": trainNum}, callback=self.parseTrain)
            yield Request(url=url_train, meta={"item": TrainItem, "num": trainNum}, callback=self.parseTrain)

    def parseTrain(self, response):
        TrainItem = response.meta["item"]
        chName    = TrainItem["ch_name"]
        trainNum  = response.meta["num"]
        trNodes   = response.xpath('//tr')
        trainDict = {}
        trainSeq = 0
        for trNode in trNodes:
            numInfo = trNode.xpath('td/text()').extract_first()
            if numInfo and numInfo.strip() == trainNum:
                #如果td中不存在数据，用td/text()取时会导致错位，直接过滤掉了无数据的td格
                trInfo = trNode.xpath('td')
                seq = int(trInfo[1].xpath('text()').extract_first())
                idleTime = 0
                if trInfo[5].xpath('text()').extract_first():
                    idleTime = transTime(trInfo[5].xpath('text()').extract_first())
                runTime = transTime(trInfo[6].xpath('text()').extract_first())
                station = trNode.xpath('td[3]/a/text()').extract_first()
                trainDict[seq] = {station: [idleTime, runTime]}
                if station == chName:
                    trainSeq = seq

        trainInfo = []
        curSeq = trainSeq + 1
        while trainDict.has_key(curSeq):
            station = trainDict[curSeq].keys()[0].encode('utf-8')
            runTime = trainDict[curSeq].values()[0][1]
            info = "{0}:{1}".format(station,(runTime-trainDict[trainSeq].values()[0][1]-trainDict[trainSeq].values()[0][0]))
            trainInfo.append(info)
            curSeq += 1

        TrainItem["train_num"] = trainNum
        TrainItem["train_info"] = trainInfo
        TrainItem["_id"] = str(uuid.uuid1())
        yield TrainItem
