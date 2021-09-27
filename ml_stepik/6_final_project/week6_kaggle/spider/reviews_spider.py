import os
import scrapy
import requests
from scrapy.crawler import CrawlerProcess
import lxml
import pandas as pd
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ReviewsSpider(scrapy.Spider):
    name = 'review-spider'
    reviews_file_name = 'data/reviews.txt'
    items_file_name = 'data/items.txt'
    root_url = 'https://irecommend.ru'

    def __init__(self):
        self.reviews_history = self.load_history(self.reviews_file_name)
        self.items_history = self.load_history(self.items_file_name)

    @staticmethod
    def load_history(fname):
        file_exists = os.path.isfile(fname)
        if file_exists:
            history = pd.read_csv(fname, sep='\t', header=None)
            history = history[0].values.tolist()
        else:
            history = []
        return history

    def start_requests(self):
        start_url = 'https://irecommend.ru/catalog/list/55'
        yield scrapy.Request(url=start_url, callback=self.parse)
        for i in range(2, 100):
            yield scrapy.Request(url=f'{start_url}?page={i}', callback=self.parse)

    def parse(self, response):
        logger.info(f'processing page {response.url}')
        item_urls = response.xpath('//a[@class="reviewsLink"]/@href').getall()
        item_urls = [i for i in item_urls if i not in self.items_history]
        for item_url in item_urls:
            yield response.follow(self.root_url + item_url,
                                  callback=self.parse_item)

    def parse_item(self, response):
        logger.info(f'processing item {response.url}')
        xpath_string = '//div[contains(@class, "woProduct")]//div[@class="reviewTitle"]/a/@href'
        review_urls = response.xpath(xpath_string).getall()
        total = len(review_urls)
        review_urls = [r for r in review_urls if r not in self.reviews_history]
        if len(review_urls) == 0:
            logger.info('ignoring item', response.url)
            self.items_history.append(response.url)
            with open(self.items_file_name, 'a') as f:
                f.write(response.url + '\n')
            return
        logger.info(f'processing {len(review_urls)} reviews of {total}')
        for review_url in review_urls:
            yield response.follow(self.root_url + review_url, callback=self.parse_review)

    def parse_review(self, response):
        logger.info(f'processing review {response.url}')
        summary = response.xpath('//a[contains(@class, "review-summary")]/text()').get()
        sections = response.xpath('//div[@itemprop="reviewBody"]/p/text()').getall()
        sections = [f for f in sections if len(f) > 1]
        sections.insert(0, summary)
        review = ' '.join(sections)
        rating = response.xpath('//meta[@itemprop="ratingValue"]/@content').get()
        self.save_review([response.url.replace(self.root_url, ''), rating, review])

    def save_review(self, s: list):
        self.reviews_history.append(s[0])
        with open(self.reviews_file_name, 'a') as f:
            f.write('\t'.join(s) + '\n')


def get_proxies():
    url = 'https://free-proxy-list.net/'
    response = requests.get(url)
    parser = lxml.html.fromstring(response.text)
    proxies = set()
    for i in parser.xpath('//tbody/tr'):
        if i.xpath('.//td[7][contains(text(), "yes")]'):
            proxy = ":".join([i.xpath('.//td[1]/text()')[0], i.xpath('.//td[2]/text()')[0]])
            proxy = 'https://' + proxy
            proxies.add(proxy)
    return proxies


settings = {
    'DOWNLOADER_MIDDLEWARES': {
        'rotating_proxies.middlewares.RotatingProxyMiddleware': 610,
        'rotating_proxies.middlewares.BanDetectionMiddleware': 620
    },
    'ROTATING_PROXY_LIST': get_proxies(),
    'LOG_LEVEL': 'INFO'
}

if not os.path.isdir('data'):
    os.mkdir('data')
logging.getLogger("scrapy").setLevel(logging.WARNING)
process = CrawlerProcess(settings=settings)
process.crawl(ReviewsSpider)
process.start()

