import os

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

import time
import pandas as pd

import boto3


# Set the AWS credentials (Make sure to set this before running!)
os.environ["AWS_ACCESS_KEY_ID"] = "your_access_key_id"
os.environ["AWS_SECRET_ACCESS_KEY"] = "your_secret_access_key"
os.environ["AWS_DEFAULT_REGION"] = "your_region"

chrome_options = Options()

#chrome_options.add_argument("--user-data-dir=/tmp/chrome_data")
chrome_options.add_argument("--disable-software-rasterizer")
chrome_options.add_argument("--headless")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--no-sandbox")

driver = webdriver.Chrome(options = chrome_options)
driver.get("https://www.rottentomatoes.com/browse/movies_in_theaters/sort:popular")

max_load_time = 120  # Maximum allowed time in seconds (2 minutes) after button press

while True:
    try:
        # Wait for the button to be present and clickable
        load_more_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@data-qa='dlp-load-more-button']"))
        )
        
        # Click the button
        load_more_button.click()
        print("Clicked 'Load More' button")
        
        # Start timing after button press
        start_time = time.time()
        
        # Wait for new content to load, but stop if it takes too long
        while time.time() - start_time < max_load_time:
            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//button[@data-qa='dlp-load-more-button']"))
                )
                break  # Exit the loop if new content is detected
            except:
                pass  # Keep waiting until max_load_time is exceeded
        else:
            print("Load process exceeded 2 minutes after button press. Stopping.")
            break
        
        # Optional: Wait a bit before checking again (to allow new content to load)
        time.sleep(2)
    
    except:
        # If the button is no longer found, break out of the loop
        print("No more 'Load More' button found. Exiting loop.")
        break

print("All content loaded or time limit reached.")

time.sleep(2)

print("saved to a file")

elements = driver.find_elements(By.CSS_SELECTOR, 'a[data-qa^="discovery-media-list-item"]')

tiles = driver.find_elements(By.CSS_SELECTOR, "[data-qa*='discovery-media-list-item-caption']")


concluding_list = []
for element in elements:
    concluding_list.append(element.get_attribute("href"))

elements2 = driver.find_elements(By.CSS_SELECTOR, "span[data-qa='discovery-media-list-item-title']")

movie_name_list =[]

for i in elements2:
    movie_name_list.append(i.text)

audience_score_list = []

for i in tiles:
    try:
        score_element = i.find_element(By.CSS_SELECTOR, 'rt-text[slot="audienceScore"]')
        score_text = score_element.text.strip()
        audience_score_list.append(score_text if score_text else None)
    except:
        audience_score_list.append(None)

critic_score_list = []

for i in tiles:
    try:
        score_element = i.find_element(By.CSS_SELECTOR, 'rt-text[slot="criticsScore"]')
        score_text = score_element.text.strip()
        critic_score_list.append(score_text if score_text else None)
    except:
        critic_score_list.append(None)



g = 0

final_list = []

for i in concluding_list:
    
    
    #add in previous lists to dict
    movie_dict = {'Movie Title': movie_name_list[g],
                  'Critic Score': critic_score_list[g],
                  'Audience Score': audience_score_list[g]}
    
    #go to the website for the specific movie
    driver.get(i)

    #grab the synopsis
    try:
        synopsis_element = driver.find_element(By.CSS_SELECTOR, 'rt-text[data-qa="synopsis-value"]')
        synopsis = synopsis_element.text.strip() if synopsis_element else None
    except:
        synopsis = None

    movie_dict['Synopsis'] = synopsis

    #grab the cast list
    cast_list = driver.find_elements(By.XPATH, "//div[p[@data-qa='person-role'][normalize-space() != 'Director']]/p[@data-qa='person-name']")

    cast_temp = ', '.join(i.text for i in cast_list)
    
    movie_dict['Cast'] = cast_temp

    #grab all other data from large "details" section on the bottom of the site
    x = driver.find_elements(By.CLASS_NAME, 'category-wrap')

    for e in x:
        cleaned_text = e.text.split()
        if len(cleaned_text) > 1:
            if cleaned_text[0] in ['Original', 'Production', 'Sound']:
                key = cleaned_text[0] + ' ' + cleaned_text[1]
                value = ' '.join(cleaned_text[2:])
            elif cleaned_text[0] in ['Aspect', 'Release', 'Rerelease']:
                key = cleaned_text[0] + ' ' + cleaned_text[1] + ' ' + cleaned_text[2]
                value = ' '.join(cleaned_text[3:])
            elif cleaned_text[0] == 'Box':
                key = cleaned_text[0] + ' ' + cleaned_text[1] + ' ' + cleaned_text[2] + ' ' + cleaned_text[3]
                value = ' '.join(cleaned_text[4:])
            else:
                key = cleaned_text[0]
                value = ' '.join(cleaned_text[1:])
        else:
            key = cleaned_text[0]
            value = ""

        movie_dict[key] = value  
    
    g += 1

    final_list.append(movie_dict)  


#convert to DF
final_df = pd.DataFrame(final_list)

#write to CSV
final_df.to_csv("rotten_tomatoes_data.csv")

bucket_name = 'practice-bucket-24'
file_key = 'rotten_tomatoes_data.csv'

s3_client = boto3.client('s3')

response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
temp_df = pd.read_csv(response.get("Body"))

combined_df = pd.concat([final_df, temp_df])
combined_df = combined_df.drop_duplicates(subset=['Movie Title', 'Director'], keep='last')


combined_df.to_csv("rotten_tomatoes_data_update.csv", index = False)

s3_client.upload_file(Bucket = bucket_name, Key = file_key, Filename= "rotten_tomatoes_data_update.csv")

driver.quit()


