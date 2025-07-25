from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Load numbers from file
with open("numbers.txt", "r") as f:
    numbers = [line.strip() for line in f.readlines()]

# Output file
output_file = open("whatsapp_active.txt", "w")

# Chrome options to suppress logs
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--log-level=3')
chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])

service = Service(executable_path="chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

# Open WhatsApp Web
print("📱 Please scan the QR code in Chrome to log in to WhatsApp Web. Then press Enter here...")
driver.get("https://web.whatsapp.com")
input()

def is_valid_whatsapp_number(number):
    try:
        # Open chat directly in WhatsApp Web
        driver.get(f"https://web.whatsapp.com/send?phone={number}")
        
        # Wait for either validation error or chat to load
        try:
            # Check for invalid number error (appears within 5 seconds)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//div[contains(text(), "Phone number shared via url is invalid.")]'))
            )
            return False
        except:
            # Check if chat interface loaded (input box exists)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//div[@role="textbox"]'))
            )
            return True
    except Exception as e:
        print(f"Error checking {number}: {str(e)}")
        return False

# Loop through numbers
for number in numbers:
    if is_valid_whatsapp_number(number):
        output_file.write(f"{number}\n")
        print(f"[✓] Valid WhatsApp: {number}")
    else:
        print(f"[✗] Invalid WhatsApp: {number}")
    
    # Small delay between checks
    time.sleep(2)

output_file.close()
driver.quit()
