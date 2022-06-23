from bs4 import BeautifulSoup
from store_scrappers.website_scrapper import WebsiteScrapper


class PingoDoceScrapper(WebsiteScrapper):
        

    def scrap(self, page_source, brand_code):
        bs = BeautifulSoup(page_source, 'lxml')
        line = dict()

        line['store'] = 'Pingo Doce'

        line['brand'] = self.brand_name_dict[brand_code]

        try:
            amount_str = bs.find('pdo-product-price-per-unit').find('span').text
            unit = amount_str.split()[1].lower()
            amount = float(amount_str.split()[0].replace(',', '.'))
            if unit == 'kg':
                amount *= 1000
            elif unit != 'g':
                raise Exception('Unexpected measurement unit')
            line['amount_g'] = amount
        except Exception:
            line['amount_g'] = None
        
        try:
            price_str = bs.find('pdo-product-price-tag').find('span').text
            price = float(price_str.split()[0].replace(',', '.'))
            line['price'] = price
        except Exception:
            line['price'] = None

        try:
            line['price_per_100g'] = price * (100 / amount)
        except Exception:
            line['price_per_100g'] = None

        return line