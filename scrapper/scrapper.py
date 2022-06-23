import json
import sys
import pandas as pd
from time import sleep
import crawler
from datetime import datetime
import sqlalchemy as db
from store_scrappers.auchan import AuchanScrapper
from store_scrappers.continente import ContinenteScrapper
from store_scrappers.pingo_doce import PingoDoceScrapper


# parameters
SLEEP_TIME = 5


class Scrapper:

    def __init__(self, jsons_folder):
        if jsons_folder is None:
            jsons_folder = 'scrapper/jsons/'
            
        self._init_dicts(jsons_folder)
        self._init_website_scrappers()


    def _init_dicts(self, jsons_folder):
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
            
            
    def _init_website_scrappers(self):
        self.website_scrappers = dict()
        
        self.website_scrappers['auchan'] = AuchanScrapper(self.brand_name_dict)
        self.website_scrappers['continente'] = ContinenteScrapper(self.brand_name_dict)
        self.website_scrappers['pingo_doce'] = PingoDoceScrapper(self.brand_name_dict)
        

    def _scrap_web_page(self, store, page_source, brand_code):
        if store in self.website_scrappers.keys():
            return self.website_scrappers[store].scrap(page_source, brand_code)
        else:
            raise Exception('Unexpected store code')
        

    def scrap(self):
        driver = crawler.get_firefox_driver()
        writer = pd.ExcelWriter('result.xlsx', engine='xlsxwriter')

        print('\n\nScraping:')
        for pt in self.catalog: # product type
            df = pd.DataFrame(columns=['store', 'brand', 'amount_g', 'price', 'price_per_100g'])
            pt_name = self.product_type_dict[pt['product_type']]

            print(f'\t{pt_name}...')
            for store in reversed(self.store_name_dict.keys()):
                for p in pt['stores'][store]:
                    try: # gambiarra to bypass infinite page loading, even though it's totally loaded
                        driver.get(p['link'])
                    except Exception:
                        pass
                    
                    sleep(SLEEP_TIME)
                    line = self._scrap_web_page(store, driver.page_source, brand_code=p['brand'])
                    if line is not None:
                        df = df.append(line, ignore_index=True)

            df.to_excel(writer, sheet_name=pt_name)

        writer.save()


    def scrap_sql(self):
        driver = crawler.get_firefox_driver()

        today = datetime.today().strftime('%Y-%m-%d')

        engine = db.create_engine('sqlite:///db.sqlite')
        metadata = db.MetaData()
        prices_table = db.Table('prices', metadata, autoload=True, autoload_with=engine)
        connection = engine.connect()

        line_list = []

        print(f'\n\nDate: {today}   Scraping:')
        for pt in self.catalog: # product type
            pt_name = self.product_type_dict[pt['product_type']]

            print(f'\t{pt_name}...')
            for store in self.store_name_dict.keys():
                for p in pt['stores'][store]:
                    try: # gambiarra to bypass infinite page loading, even though it's totally loaded
                        driver.get(p['link'])
                    except Exception:
                        pass
                    
                    sleep(SLEEP_TIME)

                    line = self._scrap_web_page(store, driver.page_source, brand_code=p['brand'])
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

    scrapper.scrap()
    
