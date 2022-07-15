from bs4 import BeautifulSoup
from numpy import product
from miner.store_files.website_scrapper import WebsiteScrapper


class ShufersalScrapper(WebsiteScrapper):
        

    def scrap(self, page_source, brand_code):
        brand_code, product_name = brand_code

        bs = BeautifulSoup(page_source, 'lxml')
        cell_list = bs.find('ul', {'id': 'mainProductGrid', 'class': 'tileContainer'})
        children = cell_list.findChildren('li', recursive=False)

        cell = None
        for cube in children:
            product_name_tag = cube.find('strong', {'data-target': '#productModal'})
            brand_code_tag = cube.find('div', {'class': 'labelsListContainer'}).find('div', {'class': 'smallText'}).find_all('span')[1]
 
            if product_name_tag.text == product_name and brand_code_tag.text == brand_code:
                cell = cube
                break
        if cell == None:
            raise Exception('Null cell')

        price_str = cell.find('span', {'class': 'price'}).find('span', {'class': 'number'}).text
        return float(price_str)