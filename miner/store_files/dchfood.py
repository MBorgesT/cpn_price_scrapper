from bs4 import BeautifulSoup
from miner.store_files.website_scrapper import WebsiteScrapper


class DCHFoodScrapper(WebsiteScrapper):
        

    def scrap(self, page_source, brand_code=None):
        bs = BeautifulSoup(page_source, 'lxml')

        try:
            product_price_block = bs.find('div', {'class': 'priceLabel discount'})
            price_str = product_price_block.find('div', {'class': 'dprice'}).text

            slash = price_str.find('/')
            if slash != -1:
                amount_str = price_str[slash + 1]
                if amount_str.isdigit():
                    amount = int(amount_str)
                else:
                    amount = 1
            else:
                amount = 1

            price_str = price_str.split()[1]
            price_str = ''.join([c for c in price_str if c in '0123456789.'])
            return float(price_str) / amount
        except Exception:
            return None