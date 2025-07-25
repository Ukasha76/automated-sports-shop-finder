from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium import webdriver
import time
import re
import os

# Create directory if it doesn't exist
if not os.path.exists("extractedShops"):
    os.makedirs("extractedShops")

# Load cities from file
with open("cities.txt", "r") as f:
    cities = [line.strip() for line in f.readlines()]

# Output files with proper encoding
log_file = open("scraping_log.txt", "w", encoding='utf-8')

# Chrome options
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--log-level=3')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

def is_valid_phone_number(text):
    """Check if text looks like a phone number"""
    phone_pattern = re.compile(r'(\+?\d[\d\- ]{7,}\d)')
    return bool(phone_pattern.search(text))

def get_phone_number(city_name):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="main"]//h1'))
        )
        time.sleep(2)
                
        phone_number = ""
        
        # Method 1: Look for elements with phone number classes
        info_elements = driver.find_elements(By.CLASS_NAME, 'Io6YTe')
        if not info_elements:
            info_elements = driver.find_elements(By.CLASS_NAME, 'fontBodyMedium')
        
        for element in info_elements:
            text = element.text.strip()
            if is_valid_phone_number(text):
                phone_number = text
                break
        
        # Method 2: Look for phone button
        if not phone_number:
            try:
                phone_button = driver.find_element(By.XPATH, '//button[contains(@aria-label, "Phone")]')
                phone_number = phone_button.get_attribute('aria-label').replace('Phone: ', '')
            except:
                pass
        
        if phone_number:
            phone_number = re.sub(r'[^\d+]', '', phone_number)
            return {
                'city': city_name,
                'phone': phone_number
            }
        
        return None
        
    except Exception as e:
        log_file.write(f"Error getting store details in {city_name}: {str(e)}\n")
        return None

def get_details(city_name, phone_numbers_file):
    try:
        driver.get(f'https://www.google.com/maps/search/sports+shops+in+{city_name}+of+united+states')
        
        # Wait for the results to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@role="feed"]'))
        )
        
        found_numbers = 0
        processed_shops = set()
        last_count = 0
        same_count_iterations = 0
        
        while True:
            # Get all currently visible shop links
            shop_links = driver.find_elements(By.XPATH, '//div[@role="feed"]//a[contains(@href, "/place/")]')
            current_count = len(shop_links)
            print(f"Visible shops: {current_count} | Processed: {len(processed_shops)}")
            
            # Check if we've reached the end (no new shops loading)
            if current_count == last_count:
                same_count_iterations += 1
                if same_count_iterations > 3:  # If count hasn't changed for 3 iterations
                    break
            else:
                same_count_iterations = 0
                last_count = current_count
            
            # Process each shop one by one
            new_shops_processed = False
            for shop in shop_links:
                shop_id = shop.get_attribute('href')
                if shop_id not in processed_shops:
                    try:
                        shop.click()
                        time.sleep(3)  # Wait for details to load
                        
                        details = get_phone_number(city_name)
                        
                        if details and details['phone']:
                            phone_numbers_file.write(f"{details['phone']}\n")
                            phone_numbers_file.flush()
                            found_numbers += 1
                            print(f"Found phone: {details['phone']}")
                        
                        # Close the details panel
                        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                        time.sleep(1)
                        processed_shops.add(shop_id)
                        new_shops_processed = True
                        
                    except Exception as e:
                        log_file.write(f"Error processing store in {city_name}: {str(e)}\n")
                        continue
            
            # If we didn't find any new shops, scroll to load more
            if not new_shops_processed:
                scrollable_element = driver.find_element(By.XPATH, '//div[@role="feed"]')
                driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollTop + arguments[0].offsetHeight;",
                    scrollable_element
                )
                time.sleep(2)  # Wait for new shops to load
        
        log_file.write(f"Found {found_numbers} numbers in {city_name}\n")
        return True
            
    except Exception as e:
        log_file.write(f"Error checking {city_name}: {str(e)}\n")
        return False

# Main loop
for city in cities:
    # Create a new file for each city
    city_file_path = os.path.join("extractedShops", f"{city}.txt")
    with open(city_file_path, "w", encoding='utf-8', newline='') as phone_numbers_file:
        if get_details(city, phone_numbers_file):
            print(f"Completed scraping for {city}")
        else:
            print(f"Failed to scrape {city}")
    time.sleep(2)

log_file.close()
driver.quit()