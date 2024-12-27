import requests
from dotenv import load_dotenv
import os

load_dotenv()

# Access variables
USERNAME      = os.getenv("ENCOMPASS_USERNAME")
PASSWORD      = os.getenv("ENCOMPASS_PASSWORD")
CLIENT_ID     = os.getenv("ENCOMPASS_CLIENTID")
CLIENT_SECRET = os.getenv("ENCOMPASS_CLIENTSECRET")
INSTANCE_ID = os.getenv("ENCOMPASS_INSTANCE")


def get_api_key():
  '''
    Makes API call to Encompass and returns access_token and token_type.
  '''
  url = "https://api.elliemae.com/oauth2/v1/token"

  payload = f'grant_type=password&username={USERNAME}%40encompass%3A{INSTANCE_ID}&password={PASSWORD}&client_id={CLIENT_ID}&client_secret={CLIENT_SECRET}'
  headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
  }

  response = requests.request("POST", url, headers=headers, data=payload)
  response = response.json()

  return response['access_token']

if __name__ == "__main__":
    print(get_api_key())