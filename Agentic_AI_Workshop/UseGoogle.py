import requests

# Replace with your actual API key and Custom Search Engine ID (CX)
API_KEY = 'AIzaSyARBfesLljB8RMlyM_7wrGLFG48dQlAElw'
CX = 'b12df274abe684b34'


def google_search(query, num_results=10):
    # Define the Google Custom Search API endpoint
    url = 'https://www.googleapis.com/customsearch/v1'

    # Set up the parameters for the request
    params = {
        'q': query,  # Search query
        'key': API_KEY,  # Your Google API key
        'cx': CX,  # Your Custom Search Engine ID
        'num': num_results,  # Number of results to fetch
    }
    try:
        # Make the API request
        response = requests.get(url, params=params)

        # If the response is successful, parse the results
        if response.status_code == 200:
            search_results = response.json()  # Parse JSON response
            return search_results['items']  # Return the list of search results
        else:
            print(f"Error: {response.status_code}")
            return None
    except:
        print(f"No search result found")

