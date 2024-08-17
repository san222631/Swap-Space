import requests
from bs4 import BeautifulSoup
import json
import os

# Define the base URL for constructing the full URL
base_url = "https://live-light.com"

# Define the headers for the HTTP requests
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

# Load existing data from the JSON file
with open(json_file_path, 'r', encoding='utf-8') as f:
    all_data = json.load(f)

# Iterate over each product in the loaded data
for product in all_data:
    # Construct the full URL using the href value
    full_url = base_url + product['href']

    # Make the GET request to the product page
    response = requests.get(full_url, headers=headers)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML response
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the <span> that contains "Size" and then find the next sibling <span> that contains the dimension
        size_label = soup.find('span', text="Size")
        dimension = None
        if size_label:
            dimension_span = size_label.find_next('span')
            if dimension_span:
                dimension = dimension_span.text.strip()
                product['dimension'] = dimension

        # Scrape the image sources from the <li> tags
        image_srcs = []
        #li_tags = soup.find_all('li', attrs={'data-target': '#o-carousel-product'})
        #for li in li_tags:
            #img_tag = li.find('img')
            #if img_tag and 'src' in img_tag.attrs:
                #image_srcs.append(img_tag['src'])
        div_tag = soup.find('div', attrs={'id': 'o-carousel-product'})
        if div_tag:
            img_tags = div_tag.find_all('img')
            for img_tag in img_tags:
                if 'src' in img_tag.attrs:
                    image_srcs.append(img_tag['src'])

        # Add the scraped image sources to the product dictionary
        if image_srcs:
            product['image_srcs'] = image_srcs

        print(f"Successfully scraped additional data for product {product['id']}")
    else:
        print(f"Failed to retrieve data from {full_url}: {response.status_code}")
        continue

# Save the updated data back to the JSON file
with open(json_file_path, 'w', encoding='utf-8') as f:
    json.dump(all_data, f, ensure_ascii=False, indent=4)

print(f"Scraping complete. Data saved to {json_file_path}")
