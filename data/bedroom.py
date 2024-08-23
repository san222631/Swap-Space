import requests
from bs4 import BeautifulSoup
import json
import os

# Define the base URL for constructing the full URL
base_url = "https://www.live-light.com"

# Define the headers for the HTTP requests
headers = {
    "authority": "www.live-light.com",
    "method": "GET",
    "scheme": "https",
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9",
    "cache-control": "no-cache",
    "cookie": "session_id=38b8385b767a3857c9c8b6c6e785258c7fc9e473",
    "dnt": "1",
    "pragma": "no-cache",
    "priority": "u=1, i",
    "referer": "https://www.live-light.com/shop/category/bedroom-10?",
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

# Load existing data from the JSON file
with open(json_file_path, 'r', encoding='utf-8') as f:
    all_data = json.load(f)

# Category to parse
category = "Bedroom"
category_url = f"https://www.live-light.com/shop/category/bedroom-10"

page = 1  # Start from page 1

# Flag to indicate if parsing should stop
stop_parsing = False

while not stop_parsing:
    # Construct the URL for the current page
    full_url = f"{category_url}/page/{page}?"

    # Make the GET request to the category page
    response = requests.get(full_url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all product links and associated onclick data
        product_links = soup.find_all('a', class_='tp-link-dark', itemprop='name')

        for link in product_links:
            onclick_data = link.get('onclick')

            if onclick_data:
                try:
                    product_info = onclick_data.split("'products': [{")[1].split("}]")[0]
                    product_id = product_info.split("'id': '")[1].split("'")[0]

                    # Find the corresponding product in the JSON data
                    for product in all_data:
                        if product['id'] == product_id:
                            # Check if the product already has the "bedroom" category
                            if 'category' in product and "bedroom" in product['category']:
                                print(f"Product {product_id} already has category 'bedroom'. Stopping parsing.")
                                stop_parsing = True
                                break

                            # Add the "bedroom" category to the product if not already present
                            if 'category' in product:
                                if "bedroom" not in product['category']:
                                    product['category'].append("bedroom")
                            else:
                                product['category'] = ["bedroom"]

                            print(f"Added 'bedroom' category to product {product_id}")

                except (IndexError, AttributeError) as e:
                    print(f"Failed to parse product info: {e}")
                    continue

        if stop_parsing:
            break

        page += 1  # Move to the next page
    else:
        print(f"Failed to retrieve data from {full_url}: {response.status_code}")
        break

# Save the updated data back to the JSON file
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print(f"Scraping complete. Data saved to {json_file_path}")
