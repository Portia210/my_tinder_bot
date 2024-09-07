import os
import json
import random
from time import sleep
from typing import List, Dict, Tuple, Optional
from dotenv import load_dotenv
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from driver import init_driver, wait_for_element
from data_to_csv import format_data_to_csv

# Constants
MAX_LIKES = 5000
NOPE_FREQUENCY = 26 # for how many people click nope
INITIAL_WAIT_TIME = 30 # how much time wait the first time the page is loaded
REFRESH_WAIT_TIME = 300 # after no more result how much time before refresh
REFRESH_ATTEMPTS = 1  # Number of refresh attempts per call (if no more results ending)
TOTAL_REFRESH_LIMIT = 1  # Total number of refresh attempts allowed

total_refreshes = 0  # Global counter for total refreshes

def load_config() -> Dict[str, str]:
    """Load configuration from .env file."""
    load_dotenv(override=True)
    return {
        "username": os.getenv("FB_USERNAME"),
        "password": os.getenv("FB_PASSWORD")
    }

def import_data() -> List[str]:
    """Load data from a JSON file and return it as a list. Create the file if it doesn't exist."""
    filename = 'matches_details.json'
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump([], f)
    with open(filename, 'r') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = []
    return data

def save_data(initial_len : int, data: List[str]) -> None:
    """Save data to JSON and CSV files."""
    with open('matches_details.json', 'w') as f:
        json.dump(data, f, indent=4)
    format_data_to_csv(data)
    print(f"Added {len(data)- initial_len} matches in matches_details.json and in output.csv")

def login_to_tinder(driver: WebDriver, config: Dict[str, str]) -> None:
    """Log in to Tinder using Facebook."""
    driver.get("https://tinder.com/")
    sleep(1)

    language_picker = wait_for_element(driver, By.CSS_SELECTOR, ".language-picker")
    driver.execute_script("arguments[0].click();", language_picker)
    en_lang = wait_for_element(driver, By.CSS_SELECTOR, 'a[lang="en"]')
    driver.execute_script("arguments[0].click();", en_lang)
    print("Changed language to English")
    sleep(1)

    login_button = driver.find_element(By.XPATH, value='//*[text()="Log in"]')
    driver.execute_script("arguments[0].click();", login_button)
    sleep(1)

    fb_login = wait_for_element(driver, By.CSS_SELECTOR, '[aria-label="Log in with Facebook"]')
    driver.execute_script("arguments[0].click();", fb_login)
    print("Entered Facebook login page")
    sleep(1)

    handle_facebook_login(driver, config)

def handle_facebook_login(driver: WebDriver, config: Dict[str, str]) -> None:
    """Handle Facebook login window."""
    WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(2))
    base_window = driver.window_handles[0]
    fb_login_window = driver.window_handles[1]
    driver.switch_to.window(fb_login_window)

    email = driver.find_element(By.XPATH, value='//*[@id="email"]')
    password = driver.find_element(By.XPATH, value='//*[@id="pass"]')
    email.send_keys(config["username"])
    password.send_keys(config["password"])
    password.send_keys(Keys.ENTER)

    try:
        continue_as = wait_for_element(driver, By.XPATH, "//div[@role='button' and (contains(@aria-label, 'Continue as'))]")
        driver.execute_script("arguments[0].click();", continue_as)
        print("Successfully logged in via Facebook")
    except TimeoutException:
        print("Problem with Facebook login, Closing it ")
        driver.close()

    sleep(1)
    try:
        WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(1))
    except TimeoutException:
        driver.close()
        WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(1))

    driver.switch_to.window(base_window)
    sleep(1)

def handle_tinder_popup(driver: WebDriver) -> None:
    """Handle Tinder pop-ups after login."""
    cookies = wait_for_element(driver, By.XPATH, '//*[text()="I accept"]')
    driver.execute_script("arguments[0].click();", cookies)
    print("Allowed Cookies")

    allow_location_button = wait_for_element(driver, By.CSS_SELECTOR, '[aria-label="Allow"]')
    driver.execute_script("arguments[0].click();", allow_location_button)
    print("Allowed location")

    notifications_button = wait_for_element(driver, By.CSS_SELECTOR, '[aria-label="I’ll miss out"]')
    driver.execute_script("arguments[0].click();", notifications_button)
    print("Disallowed notifications")

def swipe(driver: WebDriver, direction: str) -> None:
    """Swipe left or right."""
    if direction == "like":
        btn = driver.find_element(By.CSS_SELECTOR, 'div.Bdc\\(\\$c-ds-border-gamepad-like-default\\) button')
    else:
        btn = driver.find_element(By.CSS_SELECTOR, 'div.Bdc\\(\\$c-ds-border-gamepad-nope-default\\) button')
    driver.execute_script("arguments[0].click();", btn)

def get_profile_details(driver: WebDriver, wait_time: int = 8) -> Tuple[Optional[str], Optional[str]]:
    """Get profile details of the current match."""
    try:
        data_element = wait_for_element(driver, By.CSS_SELECTOR, 'div[data-keyboard-gamepad="true"][aria-hidden="false"]', wait_time)
        name_element = data_element.find_element(By.CSS_SELECTOR, '[itemprop="name"]')
        return name_element.text, data_element.text
    except NoSuchElementException:
        print("Name element not found. Proceeding with swipe anyway.")
        return None, None


def handle_out_of_matches(driver: WebDriver) -> bool:
    """Handle the case when we run out of matches."""
    global total_refreshes
    try:
        driver.find_element(By.CSS_SELECTOR, 'output[aria-busy="true"]')
        for attempt in range(REFRESH_ATTEMPTS):
            if total_refreshes >= TOTAL_REFRESH_LIMIT:
                print(f"Reached the total refresh limit of {TOTAL_REFRESH_LIMIT}. Exiting.")
                return True

            print(
                f"Run out of potential matches. Waiting {REFRESH_WAIT_TIME} seconds for more results (Attempt {attempt + 1}/{REFRESH_ATTEMPTS}, Total refreshes {total_refreshes + 1}/{TOTAL_REFRESH_LIMIT})")
            sleep(REFRESH_WAIT_TIME)
            driver.refresh()
            total_refreshes += 1

            try:
                wait_for_element(driver, By.XPATH, '//span[@itemprop="name"]', timeout=20)
                return False
            except TimeoutException:
                continue

        print(
            f"Tried {REFRESH_ATTEMPTS} times to get results but couldn't. Total refreshes: {total_refreshes}/{TOTAL_REFRESH_LIMIT}")
        return True
    except NoSuchElementException:
        print("No results and not looking for results. Unknown error. Exiting.")
        return True

def main():
    config = load_config()
    driver = init_driver(headless=True)
    matches_details = import_data()
    initial_match_amount = len(matches_details)

    try:
        login_to_tinder(driver, config)
        handle_tinder_popup(driver)

        wait_time = INITIAL_WAIT_TIME
        for n in range(MAX_LIKES):
            try:
                name, profile_details = get_profile_details(driver, wait_time)


                sleep(random.uniform(0.5, 2))

                if random.choice([True, False]) or name is None:
                    swipe(driver, "nope")
                    print(f"Nope for {name}")
                else:
                    swipe(driver, "like")
                    print(f"Like for {name}")
                    if profile_details.strip():  # Only append non-empty profile details
                        matches_details.append(profile_details)

                wait_time = 8

            except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
                element_info = getattr(e, 'msg', '')
                print(f"Exception: {e.__class__.__name__}")
                print(f"Element info: {element_info}")
                wait_time = INITIAL_WAIT_TIME
                if handle_out_of_matches(driver):
                    break

    except KeyboardInterrupt:
        print("\nKeyboard interrupt detected. Stopping gracefully...")
    finally:
        print("Saving data and closing the browser...")
        save_data(initial_match_amount, matches_details)
        driver.quit()
        print("Data saved. Program terminated.")

if __name__ == "__main__":
    main()