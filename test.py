import re
import aiohttp

from bs4 import BeautifulSoup
import scrapy
from calmjs.parse import es5
from calmjs.parse.unparsers.extractor import ast_to_dict


URL = "https://www.dtek-krem.com.ua/ua/shutdowns"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:145.0) Gecko 20100101 Firefox/145.0"
GROUP = "6.1"


class BlackoutSpider(scrapy.Spider):
    name = "blackouts"
    start_urls = [
        URL,
    ]

    def parse(self, response):
        s = response.xpath(".//script[contains(., 'DisconSchedule.fact')]")
        # s is empty when urgent blackouts !
        js_text = s.xpath(".//text()").get()

        schedules = ast_to_dict(es5(js_text))
        fact = schedules['DisconSchedule.fact']

        fact.keys()
        # dict_keys(['data', 'update', 'today'])
        fact['update']

        today_key = str(fact['today'])
        today = fact['data'][today_key] # for all groups
        current = today['GPV6.1'] # my group

        yield current

