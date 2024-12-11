import requests
from bs4 import BeautifulSoup
import re

def extract_google_search_urls(search_query):
    # encode query and create url
    query = '+'.join(search_query.split())
    url = f"https://www.google.com/search?q={query}"

    # spoof user agent
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    # if success
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # find all links
        links = soup.find_all('a', href=True)
        
        # filter out the URLs that are relevant to search results
        urls = []
        for link in links:
            url = link['href']
            # remove junk
            if not url.startswith('/') and 'google.com' not in url:
                # no duplicates, avoid google results
                if url not in urls and not url.startswith('https://www.google.'):
                    urls.append(url)
        
        return urls
    else:
        print("Failed to retrieve the page. Status code:", response.status_code)
        return []

search_query = "oral history site:.pl intitle:contact OR inurl:contact"
urls = extract_google_search_urls(search_query)
if urls:
    with open('urls.txt', 'w') as file:
        for idx, url in enumerate(urls, 1):
            print(f"{idx}. {url}")
            print(url, file=file)
else:
    print("No URLs found.")
