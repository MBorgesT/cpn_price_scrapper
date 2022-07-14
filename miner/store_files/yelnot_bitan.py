from bs4 import BeautifulSoup
from miner.store_files.website_scrapper import WebsiteScrapper


class YelnotBitanScrapper(WebsiteScrapper):
        

    def scrap(self, page_source, brand_code=None):
        bs = BeautifulSoup(page_source, 'lxml')

        try:
            price_cell = bs.find('div', {'class': 'weight-and-price'}).find('span', {'class': 'sale-price'})
            if price_cell is None:
                price_cell = bs.find('div', {'class': 'weight-and-price'}).find('span', {'class': 'price'})
           
            amount_str = price_cell.text
            amount_str = ''.join([c for c in amount_str if c in '0123456789.'])
            return float(amount_str)
        except Exception:
            return None