import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.chrome import ChromeDriverManager


def get_firefox_driver():
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


def get_chromium_driver():    
    options = webdriver.ChromeOptions()
    options.add_argument('--width=1200')
    options.add_argument('--height=700')
    options.add_argument('--disable-logging') 
    options.add_argument('--headless')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('log-level=3')

    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(
        ChromeDriverManager().install(),
        options=options
    )
    driver.set_page_load_timeout(10)

    return driver

