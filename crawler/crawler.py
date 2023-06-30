from selenium.webdriver.common.by import By
from undetected_chromedriver import Chrome
from selenium.webdriver import ChromeOptions
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import re

# Create an instance of Chrome
options = ChromeOptions()
options.add_argument('--headless')
chrome = Chrome(options=options)

# Perform scraping operations here
page_index = 1
listings_url = []
destination_page = 100
# while loop to get all listing URLs
while True and page_index < (destination_page+1):
    # Get the URL of each page
    url = f'https://batdongsan.com.vn/nha-dat-ban/p{page_index}'
    chrome.get(url)

    listings = chrome.find_elements(By.CLASS_NAME, 'js__product-link-for-product-id')
    if len(listings) < 1:
        break

    # Add the URL of each listing to a list
    for listing in listings:
        listings_url.append(listing.get_attribute('href'))

    page_index += 1  # increment the page index

# Loop through each listing
houses = []
for url in listings_url:
    try:
        chrome.get(url)

        # Close the popup if it appears
        try:
            popup = WebDriverWait(chrome, 1).until(
                EC.presence_of_element_located((By.ID, 'dialogPopup'))
            )
            close_button = popup.find_element(By.CLASS_NAME, 'close')
            close_button.click()
        except NoSuchElementException:
            pass

        listing = {}  # Create a dictionary for the current listing

        # url
        listing['url'] = url
        
        # title of the posting
        title = chrome.find_element(By.TAG_NAME, 'h1')
        listing['title'] = title.text 

        # timestamp
        time_features = chrome.find_elements(By.CSS_SELECTOR, '.re__pr-short-info-item.js__pr-config-item .value')
        try:
            posted_date = time_features[0].text
        except IndexError:
            posted_date = None

        try:
            expire_date = time_features[1].text
        except IndexError:
            expire_date = None
        listing['posted_date'] = posted_date
        listing['expire_date'] = expire_date

        # address of the listing
        address = chrome.find_element(By.CLASS_NAME, 're__pr-short-description.js__pr-address') 
        listing['address'] = address.text 

        # description
        description = chrome.find_element(By.CLASS_NAME, 're__section-body.re__detail-content.js__section-body.js__pr-description.js__tracking')
        listing['description'] = description.text 

        # features
        features = chrome.find_elements(By.CLASS_NAME, 're__pr-specs-content-item-title')
        features_info = chrome.find_elements(By.CLASS_NAME, 're__pr-specs-content-item-value')
        for i in range(len(features)):
            listing[features[i].text] = features_info[i].text

        # project
        try:
            project = chrome.find_element(By.CLASS_NAME, 're__project-title').text
            project_company = chrome.find_elements(By.CLASS_NAME, 're__long-text')[-1].text
        except NoSuchElementException:
            project = None
            project_company = None

        listing['project'] = project
        listing['project_company'] = project_company

        # images
        images = []
        try:
            next_button = chrome.find_element(By.CLASS_NAME, 're__btn.re__btn-se-border--sm.re__btn-icon--sm')
            total_images_count = int(chrome.find_element(By.CLASS_NAME, 'swiper-pagination-total').text)

            for i in range(total_images_count):
                # Get the active image element
                active_image_element = chrome.find_element(By.CSS_SELECTOR, '.swiper-slide-active .re__pr-image-cover.js__pr-image-cover')
                
                # Retrieve the image URL from the 'data-bg' attribute
                image_url = active_image_element.get_attribute('data-bg')
                if image_url == None:
                    image_url = active_image_element.get_attribute('style')
                    match = re.search(r'url\("(.*?)"\)', image_url)
                    image_url = match.group(1)
                images.append(image_url)
                
                if i < total_images_count - 1:
                    chrome.execute_script("arguments[0].click();", next_button)
                    #next_button.click

            listing['images'] = images
        except:
            listing['images'] = None

        houses.append(listing)  # Add the current listing dictionary to the house list
    except Exception as e:
        print(f"Error occurred on URL: {url}")
        print(f"Error details: {str(e)}")
        continue

# Get all unique field names including the features
fieldnames = ['title', 'address', 'description', 'project', 'project_company']
for house in houses:
    for feature in house.keys():
        if feature not in fieldnames:
            fieldnames.append(feature)

# Save data to a CSV file
filename = f'scraped_data_untilpage{destination_page}.csv'
with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(houses)

print(f"Scraped data saved to {filename}")
# Close the browser
chrome.quit()
