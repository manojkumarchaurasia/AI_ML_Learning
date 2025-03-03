from logging import exception

import requests
from bs4 import BeautifulSoup


def scrape_reviews(url):
    # Send a request to the website
    text=""
    try:
        response = requests.get(url)
        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            reviews = soup.getText()
            return reviews
        else:
           return f"Error fetching data: {response.status_code}"
    except:
        return text
# Example review page (e.g., Amazon product page)
#review_url = 'https://www.topgear.com/car-reviews/hyundai/i20'
#reviews = scrape_reviews(review_url)
#print(f"Review Text: {reviews}")

