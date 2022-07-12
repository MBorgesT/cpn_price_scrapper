from bs4 import BeautifulSoup
import re
from miner.store_files.website_scrapper import WebsiteScrapper


class ContinenteScrapper(WebsiteScrapper):
    
    
    def scrap(self, page_source, brand_code):
        bs = BeautifulSoup(page_source, 'lxml')
        line = dict()

        line['store'] = 'Continente'

        line['brand'] = self.brand_name_dict[brand_code]

        try:
            amount_str = bs.find('span', {'class': 'ct-pdp--unit'}).text
            unit = amount_str.split()[2].lower()
            amount = float(amount_str.split()[1].replace(',', '.'))
            if unit == 'kg':
                amount *= 1000
            elif unit != 'gr':
                raise Exception('Unexpected measurement unit')
            line['amount_g'] = amount
        except Exception:
            line['amount_g'] = None

        try:
            price_str = bs.find('span', {'class': 'ct-price-formatted'}).text
            price = float(re.sub('[^\d\.]', '', price_str.replace(',', '.')))
            line['price'] = price
        except Exception:
            line['price'] = None

        try:
            line['price_per_100g'] = round(price * (100 / amount), 3)
        except:
            line['price_per_100g'] = None

        return line