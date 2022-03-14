import json
import re
import sys
import pandas as pd
from bs4 import BeautifulSoup
from time import sleep
import crawler
from datetime import datetime
import sqlalchemy as db


# parameters
SLEEP_TIME = 5

class Scrapper():

    def __init__(self, jsons_folder):
        if jsons_folder is None:
            jsons_folder = 'scrapper/jsons/'
            
        self.__init_dicts(jsons_folder)


    def __init_dicts(self, jsons_folder):
        # products
        with open(f'{jsons_folder}catalog.json', 'r') as f:
            self.catalog = json.load(f)

        # dicts
        with open(f'{jsons_folder}brand_name_dict.json', 'r') as f:
            self.brand_name_dict = json.load(f)

        with open(f'{jsons_folder}product_type_dict.json', 'r') as f:
            self.product_type_dict = json.load(f)

        with open(f'{jsons_folder}store_name_dict.json', 'r') as f:
            self.store_name_dict = json.load(f)


    def __scrap_web_page(self, store, page_source, brand_code):
        if store == 'pingo_doce':
            return self.__scrap_pingo_doce(page_source, brand_code)
        elif store == 'continente':
            return self.__scrap_continente(page_source, brand_code)
        elif store == 'auchan':
            return self.__scrap_auchan(page_source, brand_code)
        else:
            raise Exception('Unexpected store code')


    def __scrap_pingo_doce(self, page_source, brand_code):
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


    def __scrap_continente(self, page_source, brand_code):
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
            line['price_per_100g'] = price * (100 / amount)
        except:
            line['price_per_100g'] = None

        return line


    def __scrap_auchan(self, page_source, brand_code):
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
            line['price_per_100g'] = price * (100 / amount)
        except:
            line['price_per_100g'] = None

        return line
        

    def scrap(self):
        driver = crawler.get_driver()
        writer = pd.ExcelWriter('result.xlsx', engine='xlsxwriter')

        print('\n\nScraping:')
        for pt in self.catalog:
            df = pd.DataFrame(columns=['store', 'brand', 'amount_g', 'price', 'price_per_100g'])
            pt_name = self.product_type_dict[pt['product_type']]

            print(f'\t{pt_name}...')
            for store in reversed(self.store_name_dict.keys()):
                for p in pt['stores'][store]:
                    try: # hack to bypass infinite page loading, even though it's totally loaded
                        driver.get(p['link'])
                    except Exception:
                        pass
                    
                    sleep(SLEEP_TIME)
                    line = self.__scrap_web_page(store, driver.page_source, brand_code=p['brand'])
                    if line is not None:
                        df = df.append(line, ignore_index=True)

            df.to_excel(writer, sheet_name=pt_name)

        writer.save()


    def scrap_sql(self):
        driver = crawler.get_driver()

        today = datetime.today().strftime('%Y-%m-%d')

        engine = db.create_engine('sqlite:///db.sqlite')
        metadata = db.MetaData()
        prices_table = db.Table('prices', metadata, autoload=True, autoload_with=engine)
        connection = engine.connect()

        line_list = []

        print(f'\n\nDate: {today}   Scraping:')
        for pt in self.catalog:
            pt_name = self.product_type_dict[pt['product_type']]

            print(f'\t{pt_name}...')
            for store in self.store_name_dict.keys():
                for p in pt['stores'][store]:
                    try: # hack to bypass infinite page loading, even though it's totally loaded
                        driver.get(p['link'])
                    except Exception:
                        pass
                    
                    sleep(SLEEP_TIME)

                    line = self.__scrap_web_page(store, driver.page_source, brand_code=p['brand'])
                    if line is not None:
                        line['date'] = today
                        line['product_type'] = pt_name
                        line_list.append(line)
        
        query = db.insert(prices_table)
        connection.execute(query, line_list)


if __name__ == '__main__':
    argv = sys.argv
    if len(argv) > 2:
        raise Exception('This program can only receive one or no arguments')
    elif len(argv) == 2:
        jsons_path = argv[1]
        json_flag = True
    else:
        json_flag = False

    scrapper = Scrapper(jsons_path if json_flag else None)

    scrapper.scrap_sql()
    
