# -*- coding: utf-8 -*-

import random
from useragents import agents 

class TrainsUaMiddleware(object):
    """change agent"""

    def process_request(self, request, spider):
        agent = random.choice(agents)
        request.headers["User-Agent"] = agent
