import requests
from bs4 import BeautifulSoup
import re
import json

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
