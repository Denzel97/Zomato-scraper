import pandas as pd
import time
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
import re
from selenium.common.exceptions import NoSuchElementException

# Function to initialize the Chrome WebDriver
def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.71 Safari/537.36'
    }

    chrome_options.add_argument(f'user-agent={headers["User-Agent"]}')
    chrome_options.add_argument(f'user-agent={headers["User-Agent"]}')

    chrome_service = ChromeService(executable_path='C:/Users/fredr/Desktop/chromedriver-win64/chromedriver.exe')
    driver = webdriver.Chrome(service=chrome_service, options=chrome_options)

    return driver

# Function to scroll to the end of the page
def scroll_to_end(driver):
    body = driver.find_element(By.TAG_NAME, 'body')
    body.send_keys(Keys.END)

# Function to wait for new content to load after scrolling
def wait_for_content_load(driver):
    time.sleep(3)  # Adjust sleep duration if needed

# Initialize the Chrome WebDriver with headless option
driver = initialize_driver()

# URL to scrape (replace with your actual URL)
url = "https://www.zomato.com/bangalore/delivery"

# Fetch dynamic content using Selenium
driver.get(url)

# Function to perform multiple scrolls to load more content
def perform_scrolls(driver, max_scroll_attempts=2):
    scroll_attempts = 0
    while scroll_attempts < max_scroll_attempts:
        scroll_to_end(driver)
        wait_for_content_load(driver)
        scroll_attempts += 1

# Perform multiple scrolls to load more content
perform_scrolls(driver)

# Lists to store data for CSV
restaurants_data = []
restaurant_details_data = []

# Extract and store information for each restaurant block
for idx, restaurant_block in enumerate(driver.find_elements(By.CLASS_NAME, 'sc-hAcydR'), start=1):
    # Extracting restaurant link
    restaurant_link_tag = restaurant_block.find_element(By.CSS_SELECTOR, 'a.sc-ePDpFu.gjRRBQ')
    restaurant_link = restaurant_link_tag.get_attribute('href')

    # Extracting restaurant name
    restaurant_name_tag = restaurant_block.find_element(By.CLASS_NAME, 'sc-1hp8d8a-0')
    restaurant_name = restaurant_name_tag.text.strip()

    # Extracting restaurant image using Selenium
    # Wait for images to load explicitly
    wait = WebDriverWait(driver, 10)
    wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'sc-s1isp7-5')))
    restaurant_image_tag = restaurant_block.find_element(By.CLASS_NAME, 'sc-s1isp7-5')
    restaurant_image = restaurant_image_tag.get_attribute('src')

    # Append data to the lists
    restaurants_data.append({'id': idx, 'name': restaurant_name, 'link': restaurant_link, 'image': restaurant_image})

    # Print restaurant details
    print(f"\nRestaurant #{idx}")
    print("Restaurant Name:", restaurant_name)
    print("Restaurant Link:", restaurant_link)
    print("Restaurant Image:", restaurant_image)
    print("----------------------------------------", "\n")

# Create DataFrame for restaurants
restaurants_df = pd.DataFrame(restaurants_data)

# Iterate through each restaurant for additional details
for idx, row in restaurants_df.iterrows():
    # Modify the restaurant link to exclude "/order" if it's present
    restaurant_link = row['link'].replace('/order', '')

    # Navigate to the modified restaurant link
    driver.get(restaurant_link)

    # Wait for the relevant content to load on the restaurant page (adjust wait time if needed)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'sc-1q7bklc-5')))

    # Extract delivery rating
    try:
        delivery_ratings_div = driver.find_element(By.XPATH,
                                                   '//div[@class="sc-1q7bklc-9 edgvoM" and contains(text(), "Delivery Ratings")]')
        delivery_rating_numeric_element = driver.find_element(By.XPATH, '(//div[@class="sc-1q7bklc-1 cILgox"])[2]')
        delivery_rating_numeric = re.search(r'\d+(\.\d+)?', delivery_rating_numeric_element.text).group()
    except NoSuchElementException:
        delivery_rating_numeric = None

    print(f"\nRestaurant #{idx}")
    print(delivery_rating_numeric)
    print("----------------------------------------", "\n")

    # Extract delivery review number
    try:
        delivery_review_div = driver.find_element(By.XPATH,
                                                  '//div[@class="sc-1q7bklc-9 edgvoM" and contains(text(), "Delivery Ratings")]')
        delivery_review_numeric_element = delivery_review_div.find_element(By.XPATH,
                                                                           './preceding-sibling::div[@class="sc-1q7bklc-8 kEgyiI"]')
        delivery_review_numeric = re.search(r'\d+(\.\d+)?', delivery_review_numeric_element.text).group()
    except NoSuchElementException:
        delivery_review_numeric = None

    # Locate the element containing location
    location_element = driver.find_element(By.XPATH, '//a[@class="sc-clNaTc vNCcy"]')
    location = location_element.text

    # Locate the element containing timings
    try:
        timings_element = driver.find_element(By.XPATH, '//span[@class="sc-kasBVs dfwCXs"]')
        timings = timings_element.text.replace('(Today)', '').strip()
    except NoSuchElementException:
        timings = None

    # Get the HTML content of the page after dynamic content is loaded
    page_source = driver.page_source

    # Define soup using BeautifulSoup
    soup = BeautifulSoup(page_source, 'html.parser')

    # Find all descendant article elements under the common section
    article_elements = soup.find_all('article')

    # Check if there is at least a second article element
    if len(article_elements) >= 2:
        # Take the second article element
        second_article_element = article_elements[1]

        # Continue with the rest of your code for extracting average cost
        try:
            # Find all p elements with class "sc-1hez2tp-0" and text starting with "₹" under the 2nd article
            average_cost_elements = second_article_element.find_all('p', class_='sc-1hez2tp-0',
                                                                    string=re.compile(r'^₹'))

            # Extract the integer value from the text and join with "₹"
            average_cost_values = ['₹' + re.search(r'₹(\d+)', element.text).group(1) for element in
                                   average_cost_elements]

            # Join the values with ", " if there are multiple values
            average_cost = ', '.join(average_cost_values) if average_cost_values else None
        except AttributeError:
            average_cost = None

        # Continue with the rest of your code for extracting popular dishes
        try:
            popular_dishes_heading = soup.find('h3', string='Popular Dishes')

            # Get the next sibling p element
            popular_dishes_element = popular_dishes_heading.find_next('p')
            popular_dishes = popular_dishes_element.text
        except AttributeError:
            popular_dishes = None

        # Find the <h3> tag with the text 'Cuisines'
        cuisines_heading = soup.find('h3', string='Cuisines')

        cuisine_names = []

        # Check if the cuisines_heading is found
        if cuisines_heading:
            # Get the parent <section> containing the cuisines section
            cuisines_section = cuisines_heading.find_next('section')

            # Extract cuisine names
            cuisine_names = [a_tag.text for a_tag in cuisines_section.find_all('a')]

        # Find the <h3> tag with the text 'Known For'
        known_for_heading = soup.find('h3', string='People Say This Place Is Known For')

        # Check if the known_for_heading is found
        if known_for_heading:
            # Get the next sibling p element
            known_for_element = known_for_heading.find_next('p')
            known_for_info = known_for_element.text.strip()
        else:
            known_for_info = None

        # Append data to the restaurant_details_data list
        restaurant_details_data.append({
            'id': idx + 1,
            'restaurant known for': known_for_info,
            'delivery_rating': delivery_rating_numeric,
            'delivery_review_number': delivery_review_numeric,
            'location': location,
            'timings': timings,
            'average_price': average_cost,
            'Dishes': popular_dishes,
            'cuisines': cuisine_names
        })

# Create DataFrame for restaurant details
restaurant_details_df = pd.DataFrame(restaurant_details_data)

# Save DataFrames to CSV files
restaurants_df.to_csv('restaurants_data.csv', index=False)
restaurant_details_df.to_csv('restaurant_details_data.csv', index=False)

# Close the WebDriver
driver.quit()