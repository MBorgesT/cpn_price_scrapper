from bs4 import BeautifulSoup
from miner.store_files.website_scrapper import WebsiteScrapper


class ParkNShopScrapper(WebsiteScrapper):
        

    def scrap(self, page_source, brand_code=None):
        bs = BeautifulSoup(page_source, 'lxml')

        try:
            price_group = bs.find('div', {'class': 'product-price-group'})
            price_txt = price_group.find('span', {'class': 'currentPrice'}).text
            price_txt = ''.join([c for c in price_txt if c in '0123456789.'])
            normal_price  = float(price_txt)

            special_offer_div = bs.find('div', {'class': 'product-special-offer'})
            if special_offer_div is not None:
                offer_price_txt = special_offer_div.find('span', {'class': 'offer-price'}).text
                offer_price_txt = ''.join([c for c in offer_price_txt if c in '0123456789.'])
                offer_price = float(offer_price_txt)
            else:
                offer_price = None
            
            return normal_price, offer_price
        except Exception:
            return None