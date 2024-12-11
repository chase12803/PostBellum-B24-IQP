import requests
from bs4 import BeautifulSoup
import re
import json

# SerpAPI configuration
SEARCH_ENGINE = "https://serpapi.com/search.json"
SEARCH_QUERY = '"contact" OR "email" AND "oral history"'
RESULTS_PER_PAGE = 10
MAX_PAGES = 10

def get_google_search_results(query, api_key, num_results=RESULTS_PER_PAGE, start=0):
    """Fetch search results from Google using SerpAPI."""
    params = {
        "q": query,
        "api_key": api_key,
        "num": num_results,
        "start": start
    }
    response = requests.get(SEARCH_ENGINE, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching search results: {response.status_code}")
        return None

def scrape_emails_from_url(url):
    """Scrape email addresses from a given URL."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            text = ''
            for d in soup:
                text += d.get_text(' ')
            # Improved regex to match emails in plain text and mailto: links
            email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
            emails = set(re.findall(email_pattern, text))
            
            # convert to lowercase and make them all lowercase
            emails = {x.lower() for x in emails if x not in ['user@domain.com', 'customerservice@publishingconcepts.com']}

            return list(emails) if emails else ["failed"]
        else:
            print(f"Failed to scrape {url}: {response.status_code}")
            return ["failed"]
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ["failed"]

def main():
    # try:
    #     with open('api_key.txt', 'r') as file:
    #         SERP_API_KEY = file.read()
    # except FileNotFoundError:
    #     print("API key file not found.")
    #     input("Press enter to exit.")
    #     exit()
    
    urls = []
    
    try:
        with open('urls.txt', 'r') as file:
            urls = file.readlines()
    except FileNotFoundError:
        print("URL file not found.")
        input("Press enter to exit.")
        exit()
        
    urls = [x.strip() for x in urls]   
    email_data = []
    
    # for page_num in range(MAX_PAGES):
    #     start = page_num * RESULTS_PER_PAGE
    #     print(f"Fetching results for page {page_num + 1}...")
        
    #     # Fetch search results from SerpAPI
    #     search_results = get_google_search_results(SEARCH_QUERY, SERP_API_KEY, num_results=RESULTS_PER_PAGE, start=start)
        
    #     if not search_results or "organic_results" not in search_results:
    #         print("No search results fetched. Exiting.")
    #         break

    #     # Process search results
    #     for result in search_results.get("organic_results", []):
    #         link = result.get("link")
    #         print(f"Processing: {link}")
    #         # Scrape emails from the webpage
    #         emails = scrape_emails_from_url(link)
    #         email_data.append({
    #             "webpage": link,
    #             "emails": emails
    #         })
    
    for url in urls:
        emails = scrape_emails_from_url(url)
        
        
        email_data.append({
            "webpage": url,
            "emails": emails if emails else ['failed']
        })
    
    # Save results to a JSON file
    out_file = input("Output File Name: ")
    print("Saving results...")
    with open(f'{out_file}.json', "w", encoding="utf-8") as f:
        json.dump(email_data, f, indent=4)
    print(f"Results saved to {out_file}.json'")

if __name__ == "__main__":
    main()
