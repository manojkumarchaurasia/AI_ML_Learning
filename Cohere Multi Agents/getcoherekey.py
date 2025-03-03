# pip install cohere

import cohere
import json
import os

# Get your free API key: https://dashboard.cohere.com/api-keys
API_KEY = os.getenv('API_KEY') # get in your Cohere API key here from envoirnment variable
#API_KEY = "xjG5F5HbcF49gmKKYShwGRkndnSaJ4Gnc2HONg9m"  # fill in your Cohere API key here
co = cohere.ClientV2(API_KEY)

print('API_KEY :',{API_KEY})

# Add the user message
message = "I'm joining a new startup called Co1t today. Could you help me write a short introduction message to my teammates."
# Generate the response
response = co.chat(
    model="command-r-plus-08-2024",
    messages=[{"role": "user", "content": message}],
)
#    messages=[cohere.UserMessage(content=message)])
print(response.message.content[0].text)