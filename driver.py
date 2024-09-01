from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def init_driver(headless = True):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_experimental_option("detach", True)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_argument("accept-language=en-US;q=0.8,en;q=0.7")
    chrome_options.add_argument('--log-level=ALL')
    if headless:
        chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')  # Usually recommended for headless mode
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--proxy-server="direct://"')
    chrome_options.add_argument('--proxy-bypass-list=*')
    chrome_options.add_argument('--start-maximized')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--log-level=1')  # Set log level (1 = INFO, 0 = DEBUG)
    chrome_options.add_argument('--disable-logging')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--v=1')
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


