import json
import os
import sys
import io
import time
from attrs import asdict
import pandas as pd
from time import sleep
from datetime import datetime
import sqlalchemy as db
from tqdm import tqdm
from miner import crawler
from miner.store_files.auchan import AuchanScrapper
from miner.store_files.continente import ContinenteScrapper
from miner.store_files.pingo_doce import PingoDoceScrapper
from miner.store_files.yelnot_bitan import YelnotBitanScrapper
from miner.store_files.hazi_hinam import HaziHinamScrapper
from miner.store_files.shufersal import ShufersalScrapper


# parameters
SLEEP_TIME = 6


def clear():
    os.system('cls' if os.name=='nt' else 'clear')


class Scrapper:

    def __init__(self, catalog, jsons_folder):
        if jsons_folder is None:
            jsons_folder = 'miner/jsons/'
            
        self._init_dicts(catalog, jsons_folder)
        self._init_website_scrappers()


    def _init_dicts(self, catalog, jsons_folder):
        # products
        with open(f'{jsons_folder}catalog_{catalog}.json', 'r', encoding='utf-8') as f:
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

        self.website_scrappers['yelnot_bitan'] = YelnotBitanScrapper(None)
        self.website_scrappers['hazi_hinam'] = HaziHinamScrapper(None)
        self.website_scrappers['shufersal'] = ShufersalScrapper(None)
        

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


    def _get_shufersal_html(self, driver):
        driver.get('https://www.shufersal.co.il/online/he/%D7%A7%D7%98%D7%92%D7%95%D7%A8%D7%99%D7%95%D7%AA/%D7%A1%D7%95%D7%A4%D7%A8%D7%9E%D7%A8%D7%A7%D7%98/%D7%91%D7%99%D7%A9%D7%95%D7%9C-%D7%90%D7%A4%D7%99%D7%94-%D7%95%D7%A9%D7%99%D7%9E%D7%95%D7%A8%D7%99%D7%9D/%D7%A9%D7%99%D7%9E%D7%95%D7%A8%D7%99%D7%9D/c/A2217?q=:relevance:categories-4:A221716')
        
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            # Scroll down to bottom
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            # Wait to load page
            time.sleep(2)

            # Calculate new scroll height and compare with last scroll height
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        return driver.page_source

    def scrap_portugal(self):
        driver = crawler.get_chromium_driver()
        today = datetime.today().strftime('%Y-%m-%d')
        try:
            writer = pd.ExcelWriter(f'{today}-portugal-prices.xlsx', engine='xlsxwriter')
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


    def scrap_israel(self, country):
        driver = crawler.get_chromium_driver()
        today = datetime.today().strftime('%Y-%m-%d')
        try:
            writer = pd.ExcelWriter(f'{today}-{country}-prices.xlsx', engine='xlsxwriter')
        except PermissionError:
            raise PermissionError('Please close the results file before running the program')

        shufersal_page_source = self._get_shufersal_html(driver)

        clear()
        df = pd.DataFrame(columns=['Brand', 'Fish', 'Product', 'Yelnot Bitan', 'Hazi Hinam'])
        print('\tScraping...')
        with tqdm(total=len(self.catalog)) as pbar:
            for product in self.catalog: # product
                line = dict()
                line['Brand'] = product['product']
                line['Fish'] = product['fish']
                line['Product'] = product['brand']
                
                for store in product['stores']:
                    if store['name'] == 'shufersal':
                        page_source = shufersal_page_source
                    else:
                        try: # gambiarra to bypass infinite page loading, even though it's totally loaded
                            driver.get(store['link'])
                        except Exception:
                            pass
                        sleep(SLEEP_TIME)
                        page_source = driver.page_source
                        
                    if store['name'] == 'yelnot_bitan':
                        brand_code = None
                    elif store['name'] == 'hazi_hinam':
                        brand_code = store['product_name']
                    else: # shufersal:
                        brand_code = (store['brand_code'], store['product_name'])
                    
                    line[self.store_name_dict[store['name']]] = self._scrap_web_page(
                        store['name'], 
                        page_source, 
                        brand_code
                    )

                df = pd.concat([df, pd.DataFrame([line])], axis=0, ignore_index=True)
                pbar.update(1)

        df.to_excel(writer)
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

