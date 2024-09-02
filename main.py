import os
from time import sleep
from dotenv import load_dotenv
import json
from selenium.common import TimeoutException
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import random
from driver import init_driver, wait_for_element

load_dotenv(override=True)
USERNAME = os.getenv("FB_USERNAME")
PASSWORD = os.getenv("FB_PASSWORD")
print(USERNAME, PASSWORD)

with open("matches_details.json") as file:
    matches_details = json.load(file)

driver = init_driver(headless=True)

print("please wait for Tinder to load...")
print("----------------------------------------")
driver.get("https://tinder.com/")
sleep(2)
# Create an instance of ActionChains
actions = ActionChains(driver)

# accept_cookies = wait_for_element(driver, By.XPATH, '//*[@id="c-2079390956"]/div/div[2]/div/div/div[1]/div[1]/button/div[2]/div[2]/div')
# accept_cookies.click()

language_picker = wait_for_element(driver, By.CSS_SELECTOR, ".language-picker")
driver.execute_script("arguments[0].click();", language_picker)
sleep(0.5)
en_lang = driver.find_element(By.CSS_SELECTOR, 'a[lang="en"]')
driver.execute_script("arguments[0].click();", en_lang)
print("changed lang")
sleep(1)
login_button = driver.find_element(By.XPATH, value='//*[text()="Log in"]')
driver.execute_script("arguments[0].click();", login_button)

sleep(1)
fb_login = wait_for_element(driver, By.CSS_SELECTOR, '[aria-label="Log in with Facebook"]')
driver.execute_script("arguments[0].click();", fb_login)
print("enter to fb login page")

sleep(1)
# Wait for the new window to open
WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(2))
base_window = driver.window_handles[0]
fb_login_window = driver.window_handles[1]
driver.switch_to.window(fb_login_window)

# Login and hit enter
email = driver.find_element(By.XPATH, value='//*[@id="email"]')
password = driver.find_element(By.XPATH, value='//*[@id="pass"]')
email.send_keys(USERNAME)
password.send_keys(PASSWORD)
password.send_keys(Keys.ENTER)

try:
    continue_as = wait_for_element(driver, By.XPATH,
                                   "//div[@role='button' and (contains(@aria-label, 'המשך בתור') or contains(@aria-label, 'Continue as'))]")
    driver.execute_script("arguments[0].click();", continue_as)
    print("success fb login")
except TimeoutException:
    print("problem with facebook login, close it manually")
    driver.close()
sleep(1)
# Wait for the new window to open
try:
    WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(1))
except TimeoutException:
    driver.close()
    WebDriverWait(driver, 20).until(EC.number_of_windows_to_be(1))


driver.switch_to.window(base_window)

sleep(1)

# Allow cookies
cookies = wait_for_element(driver, By.XPATH, '//*[text()="I accept"]')
driver.execute_script("arguments[0].click();", cookies)

# Allow location
allow_location_button = wait_for_element(driver, By.CSS_SELECTOR, '[aria-label="Allow"]')
driver.execute_script("arguments[0].click();", allow_location_button)
print("allow location")

# Disallow notifications
notifications_button = wait_for_element(driver, By.CSS_SELECTOR, '[aria-label="I’ll miss out"]')
driver.execute_script("arguments[0].click();", notifications_button)
print("allow notification")

click_interceptions = 0
refresh_counter = 0
finish_program = False

# Tinder free tier only allows 100 "Likes" per day. If you have a premium account, feel free to change to a while loop.
data_element = wait_for_element(driver, By.CSS_SELECTOR, 'div[data-keyboard-gamepad="true"][aria-hidden="false"]', timeout=40)
for n in range(5000):
    try:
        # Check if name and age exist
        data_element = wait_for_element(driver, By.CSS_SELECTOR, 'div[data-keyboard-gamepad="true"][aria-hidden="false"]', timeout=8)
        name = data_element.find_element(By.CSS_SELECTOR, '[itemprop="name"]').text
        all_details = data_element.text


        random_sec = round(random.uniform(0.5, 1.2), 1)
        sleep(random_sec)

        link_btn = driver.find_element(By.CSS_SELECTOR, 'div.Bdc\\(\\$c-ds-border-gamepad-like-default\\) button')
        nope_btn = driver.find_element(By.CSS_SELECTOR, 'div.Bdc\\(\\$c-ds-border-gamepad-nope-default\\) button')
        if n % 26 == 0 and n != 0 :
            # click on nope
            driver.execute_script("arguments[0].click();", nope_btn)

            print("Nope")
        else:
            # click on like
            driver.execute_script("arguments[0].click();", link_btn)

            print(f"Clicked Like for {name}")
            matches_details.append(all_details)

        if n % 20 == 0:
            # Store the list in a JSON file
            with open('matches_details.json', 'w') as f:
                json.dump(matches_details, f, indent=4)
        click_interceptions = 0

    #deal with cases that couldn't click the btn
    except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e:
        print(f"{e.__class__.__name__}")

        try:
            driver.find_element(By.CSS_SELECTOR, 'output[aria-busy="true"]')


            while True:
                print("run out of potential matches, let's refresh")
                seconds_to_wait = 600
                print(f"waiting {seconds_to_wait} for more results")
                sleep(seconds_to_wait)
                driver.refresh()
                try:
                    wait_for_element(driver, By.XPATH, '//span[@itemprop="name"]', timeout=20)
                    break
                except TimeoutException:
                    refresh_counter += 1
                    if refresh_counter == 3:
                        print("tried 3 times to get results but couldn't, exiting")
                        finish_program = True
                        break
            if finish_program:
                break

        except NoSuchElementException:
            print("no result and not looking for results")
            print("unknown error, no more matches, and not looking as well")
            break




    except Exception as e:
        print(f"couldn't like\nOther Exception: {e}")

        click_interceptions += 1
        if click_interceptions == 3:
            break
        continue




# Store the list in a JSON file
with open('matches_details.json', 'w') as f:
    json.dump(matches_details, f, indent=4)

print(f"Stored {len(matches_details)} matches in matches_details.json")

driver.quit()
