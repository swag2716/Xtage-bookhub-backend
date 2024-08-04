import requests

def fetch_books_from_google_books(query, max_results=10):
    url = f'https://www.googleapis.com/books/v1/volumes?q={query}&maxResults={max_results}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('items', [])
    else:
        return []
