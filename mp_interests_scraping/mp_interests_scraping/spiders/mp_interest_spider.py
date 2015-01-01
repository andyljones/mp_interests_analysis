# -*- coding: utf-8 -*-
import scrapy
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule

from mp_interests_scraping.items import MpInterestsScrapingItem

class MpInterestSpiderSpider(CrawlSpider):
    name = 'mp_interest_spider'
    allowed_domains = ['publications.parliament.uk']
    start_urls = ['http://www.publications.parliament.uk/pa/cm/cmregmem/contents1415.htm']    
#    start_urls = ['http://www.publications.parliament.uk/pa/cm/cmregmem/141208/part1contents.htm']

    rules = (
        Rule(LinkExtractor(allow=".*/cmregmem/\d*/.*_.*.htm"), callback='parse_item'),
        Rule(LinkExtractor(allow=".*/cmregmem/\d*/part1contents.htm")),
    )
    
    def parse_item(self, response):
        item = MpInterestsScrapingItem()
        item['url'] = response.url
        item['main_text'] = response.css("#mainTextBlock").extract()
        
        return item
