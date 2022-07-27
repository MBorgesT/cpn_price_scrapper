from bs4 import BeautifulSoup
from miner.store_files.website_scrapper import WebsiteScrapper


class CitySuperScrapper(WebsiteScrapper):
        

    def scrap(self, page_source, brand_code=None):
        bs = BeautifulSoup(page_source, 'lxml')

        try:
            product_price_block = bs.find('div', {'class': 'product-single__form-price'})
            price_str = product_price_block.find('span', {'class': 'visually-hidden'}).text
            price_str = ''.join([c for c in price_str if c in '0123456789.'])
            return float(price_str)
        except Exception:
            return None