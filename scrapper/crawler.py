from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.firefox import GeckoDriverManager


def get_driver():
    options = webdriver.FirefoxOptions()
    options.add_argument('--width=1200')
    options.add_argument('--height=700')
    options.add_argument('--disable-logging') 
    options.add_argument('--headless')
    s = Service(GeckoDriverManager().install())
    driver = webdriver.Firefox(
        service=s, 
        options=options
    )
    driver.set_page_load_timeout(10)
    return driver