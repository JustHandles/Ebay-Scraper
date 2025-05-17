from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

def get_ebay_image_urls(ebay_url):
    """Fetch image URLs from an eBay listing using Selenium."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in background
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    
    print(f"Fetching images from: {ebay_url}")
    driver.get(ebay_url)
    time.sleep(5)  # Wait for page to load

    image_urls = []
    
    try:
        # Find all images in the listing (Modify if necessary)
        images = driver.find_elements(By.CSS_SELECTOR, "img.s-item__image-img")

        for img in images:
            src = img.get_attribute("src")
            if src:
                image_urls.append(src)

    except Exception as e:
        print(f"Error fetching images: {e}")

    driver.quit()
    return image_urls  # Return the list of images
