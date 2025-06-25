import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = "https://newsdata.io/api/1/news"

def fetch_articles_from_api(language="en", country=None, category=None):
    params = {
        "apikey": API_KEY,
        "language": language
    }
    if country:
        params["country"] = country
    if category:
        params["category"] = category

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if response.status_code != 200 or data.get("status") == "error":
            print("API error:", response.status_code, data)
            return []

        print(f"Fetched {len(data.get('results', []))} articles.")
        return data.get("results", [])

    except Exception as e:
        print("Error fetching articles from API:", e)
        return []