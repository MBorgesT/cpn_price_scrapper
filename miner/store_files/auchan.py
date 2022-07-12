from bs4 import BeautifulSoup
from miner.store_files.website_scrapper import WebsiteScrapper


class AuchanScrapper(WebsiteScrapper):
    
    
    def scrap(self, page_source, brand_code):
        bs = BeautifulSoup(page_source, 'lxml')

        add_button = bs.find('button', {'class': 'auc-button__rounded auc-button__rounded--primary auc-js-add-to-cart'})
        if add_button is None:
            return None

        line = dict()

        line['store'] = 'Auchan'

        line['brand'] = self.brand_name_dict[brand_code]

        try:
            attribute_list = bs.find('div', {'id': 'collapsible-attributes-1', 'class': 'col-12 value content auc-pdp__accordion-body auc-pdp__attribute-container'})
            amount_str = attribute_list.findChildren('ul', recursive=False)[0].findChildren('li', recursive=False)[0].text
            unit = amount_str.split()[1].lower()
            amount = float(amount_str.split()[0].replace(',', '.'))
            if unit == 'kg':
                amount *= 1000
            elif unit != 'gr' and unit != 'g':
                raise Exception('Unexpected measurement unit')
            line['amount_g'] = amount
        except Exception:
            line['amount_g'] = None

        try:
            price_str = bs.find('div', {'class': 'prices auc-pdp-price auc-pdp__price float-left'}).find('span', {'class': 'value'})['content']
            price = float(price_str)
            line['price'] = price
        except Exception:
            line['price'] = None

        try:
            line['price_per_100g'] = round(price * (100 / amount), 3)
        except:
            line['price_per_100g'] = None

        return line