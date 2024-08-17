import requests
from bs4 import BeautifulSoup
import json
import os

# Define the base URL for the API request
base_url = "https://live-light.com/shop/page/{}?"

# Define the headers including cache and session
headers = {
    "authority": "live-light.com",
    "method": "GET",
    "scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "cookie": "session_id=286521b282bd5ddd9ab049368722cc352dd75875",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://live-light.com/shop?",
    "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
    "x-requested-with": "XMLHttpRequest"
}

# Path to the existing JSON file
json_file_path = os.path.join('data', 'data.json')

all_data = []
seen_ids = set()  # Set to track seen product ids

# Specify the number of pages to scrape
total_pages = 20  # Adjust this number based on how many pages you need to scrape

for page in range(1, total_pages + 1):
    # Construct the URL for the current page
    url = base_url.format(page)

    # Make the GET request to the URL
    response = requests.get(url, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract the 'description' content from the meta tag
        description_meta = soup.find('meta', itemprop='description')
        description = description_meta['content'] if description_meta else ''

        # Find all the relevant <a> tags with the necessary attributes
        product_links = soup.find_all('a', class_='d-block h-100', itemprop='url')
        for link in product_links:
            href = link.get('href')
            onclick_data = link.get('onclick')
            
            # Extract product details from the onclick data
            if onclick_data:
                # A simple way to parse the string content of onclick
                try:
                    product_info = onclick_data.split("'products': [{")[1].split("}]")[0]
                    name = product_info.split("'name': '")[1].split("'")[0]
                    product_id = product_info.split("'id': '")[1].split("'")[0]
                    price = product_info.split("'price': '")[1].split("'")[0]
                except (IndexError, AttributeError):
                    continue  # Skip this product if parsing fails
                
                # Check if the product_id has been seen before
                if product_id in seen_ids:
                    print(f"Duplicate id '{product_id}' found on page {page}. Stopping the scraping process.")
                    break  # Stop the scraping process if duplicate id is found

                # Store the scraped data in a dictionary
                data = {
                    "description": description,
                    "href": href,
                    "name": name,
                    "id": product_id,
                    "price": price
                }
                # Append the dictionary to the all_data list
                all_data.append(data)
                
                # Add the product_id to the set of seen ids
                seen_ids.add(product_id)
        
        else:
            print(f"Successfully scraped page {page}")
            continue  # Continue if no break occurred

        break  # Exit the loop if break was triggered

    else:
        print(f"Failed to retrieve data from page {page}: {response.status_code}")
        continue

# Save the updated data back to the JSON file
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print(f"Scraping complete. Data saved to {json_file_path}")
