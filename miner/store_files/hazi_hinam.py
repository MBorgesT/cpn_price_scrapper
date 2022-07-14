from bs4 import BeautifulSoup
from numpy import product
from miner.store_files.website_scrapper import WebsiteScrapper


class HaziHinamScrapper(WebsiteScrapper):
        

    def scrap(self, page_source, brand_code):
        bs = BeautifulSoup(page_source, 'lxml')

        #cell = bs.find('h3', text=brand_code).parent.parent

        cell = None
        for cube in bs.find('div', {'class': 'product_cubes'}).findChildren('app-product-cube', recursive=False):
            product_name_tag = cube.find('h3', {'class': 'product-cube-name'})
            if product_name_tag.find(text=True, recursive=False) == brand_code:
                cell = cube
                break
        if cell == None:
            raise Exception('Null cell')

        price_str = cell.find('div', {'class': 'product_cube-price'}).text
        price_str = ''.join([c for c in price_str if c in '0123456789.,'])
        price_str = price_str.split('.')[0].replace(',', '.')
        return float(price_str)