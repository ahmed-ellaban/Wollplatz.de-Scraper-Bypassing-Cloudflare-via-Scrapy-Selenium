# encoding: utf-8
import json
import os
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse
from undetected_chromedriver import Chrome



brands = ['DMC', 'Drops', 'Drops', 'Hahn', 'Stylecraft']
names = ['Natura XL',
         'Safran',
         'Baby Merino Mix',
         'Alpacca Speciale',
         'Special double knit']


class selenium_middleware:
    def __init__(self):
        self.driver = Chrome(headless=False, use_subprocess=False)

    def process_request(self, request, spider):
        if request.meta.get('selenium'):
            self.driver.get(request.url)
            self.driver.implicitly_wait(10)
            return HtmlResponse(
                self.driver.current_url,
                body=self.driver.page_source,
                encoding='utf-8',
                request=request
            )

    def spider_closed(self):
        self.driver.quit()

class SpiderWollplatz(scrapy.Spider):
    name = "wollplatz"

    def start_requests(self):
        for brand, name in zip(brands, names):
            yield scrapy.Request(
                f"https://dynamic.sooqr.com/suggest/script/?searchQuery={brand}%20{name}&view=44898be26662b0df&account=SQ-119572-1",
                callback=self.parse, dont_filter=True)

    def parse(self, response):
        data = response.text.replace(
            """websight.sooqr.instances['SQ-119572-1'].searchCallback.sendSearchQueryByScriptCompleted(""", '').replace(
            ');', '')
        # convert text response to json
        data_json = json.loads(data)
        # convert the html content to scrapy object
        if data_json['resultsPanel'].get('html'):
            response = HtmlResponse(url='', body=data_json['resultsPanel']['html'], encoding='utf-8')
            url = response.css('a.productlist-imgholder::attr(href)').get()
            ## this request gave 403 and not way to avoid javascript handling so I will use selenium
            yield response.follow(url, callback=self.parse_product, meta={'selenium': True})
        else:
            self.logger.error(f'No results found for url; {response.url}')

    def parse_product(self, response):
        price = response.css('.product-price-amount::text').get()
        availability = bool(response.css('meta[content="http://schema.org/InStock"]'))
        composition = response.xpath("//tr[contains(.,'Zusammenstellung')]/td[2]/text()").get()
        needle = response.xpath("//tr[contains(.,'Nadelstärke')]/td[2]/text()").get()
        yield {
            'Price': price,
            'Availability': availability,
            'Composition': composition,
            'Needle Size': needle,
            'URL': response.url
        }


if __name__ == "__main__":
    Settings = {

        'FEED_EXPORTERS': {

            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'FEEDS': {os.path.join('result folder', 'wollplatz result.xlsx'): {
            'format': 'xlsx',
        }},
        # 'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': True,
        'COOKIES_DEBUG ': True,
        # 'DOWNLOAD_DELAY': 0,
        # 'CONCURRENT_REQUESTS': 5,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
        # 'CONCURRENT_ITEMS': 100,
        # 'DOWNLOAD_TIMEOUT': 100,
        # 'RANDOMIZE_DOWNLOAD_DELAY': True,
        'DOWNLOADER_MIDDLEWARES': {
            'wollplatz-scraper-task.selenium_middleware': 543,
        },
        'HTTPCACHE_ENABLED': True,
        'HTTPCACHE_IGNORE_HTTP_CODES': [400, 403, 404, 413, 414, 429, 456, 503, 529, 500],
        'DEFAULT_REQUEST_HEADERS': {
            'accept': '*/*',
            'accept-language': 'ar,ar-EG;q=0.9,en-GB;q=0.8,en;q=0.7,fr-FR;q=0.6,fr;q=0.5,en-US;q=0.4',
            'cache-control': 'no-cache',
            'pragma': 'no-cache',
            'referer': 'https://www.wollplatz.de/',
            'sec-ch-ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'script',
            'sec-fetch-mode': 'no-cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
        },
    }
    process = CrawlerProcess(Settings)
    process.crawl(SpiderWollplatz)
    process.start()

"""
 Created by [Ahmed Ellaban](https://upwork.com/freelancers/ahmedellban)
وَسَلَامٌ عَلَى الْمُرْسَلِينَ وَالْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ 
"""
