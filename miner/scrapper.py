import json
import os
import sys
import io
import pandas as pd
from time import sleep
from datetime import datetime
import sqlalchemy as db
from tqdm import tqdm
from miner import crawler
from miner.store_files.auchan import AuchanScrapper
from miner.store_files.continente import ContinenteScrapper
from miner.store_files.pingo_doce import PingoDoceScrapper


# parameters
SLEEP_TIME = 6


def clear():
    os.system('cls' if os.name=='nt' else 'clear')

# Disable
def blockPrint():
    sys.stdout = io.BytesIO()
    sys.stderr = io.BytesIO()

# Restore
def enablePrint():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stdout__


class Scrapper:

    def __init__(self, jsons_folder):
        if jsons_folder is None:
            jsons_folder = 'miner/jsons/'
            
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


    def _get_n_products_by_pt(self, pt):
        for aux_pt in self.catalog:
            if aux_pt['product_type'] == pt:
                n = 0
                for _, p_list in aux_pt['stores'].items():
                    n += len(p_list)
                return n
        raise Exception('Invalid product type')
        

    def scrap(self):
        driver = crawler.get_chromium_driver()
        today = datetime.today().strftime('%Y-%m-%d')
        try:
            writer = pd.ExcelWriter(f'{today}-prices.xlsx', engine='xlsxwriter')
        except PermissionError:
            raise PermissionError('Please close the results file before running the program')

        clear()
        print('Scraping:')
        for pt in self.catalog: # product type
            df = pd.DataFrame(columns=['store', 'brand', 'amount_g', 'price', 'price_per_100g'])
            pt_name = self.product_type_dict[pt['product_type']]

            print(f'\n\t{pt_name}...')
            with tqdm(total=self._get_n_products_by_pt(pt['product_type'])) as pbar:
                for store in reversed(self.store_name_dict.keys()):      
                    if store not in pt['stores'].keys():
                        pbar.update(1)
                        continue

                    for p in pt['stores'][store]:
                        try: # gambiarra to bypass infinite page loading, even though it's totally loaded
                            driver.get(p['link'])
                        except Exception:
                            pass
                        
                        if store == 'pingo_doce':
                            sleep(SLEEP_TIME)
                        
                        line = self._scrap_web_page(store, driver.page_source, brand_code=p['brand'])
                        if line is not None:
                            df = pd.concat([df, pd.DataFrame([line])], axis=0, ignore_index=True)

                        pbar.update(1)

            df.to_excel(writer, sheet_name=pt_name)

        writer.save()


    def scrap_sql(self):
        driver = crawler.get_chromium_driver()

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
                    
                    if store == 'pingo_doce':
                        sleep(SLEEP_TIME)

                    line = self._scrap_web_page(store, driver.page_source, brand_code=p['brand'])
                    if line is not None:
                        line['date'] = today
                        line['product_type'] = pt_name
                        line_list.append(line)
        
        query = db.insert(prices_table)
        connection.execute(query, line_list)

