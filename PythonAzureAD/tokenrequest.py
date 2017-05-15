import IPython.display
import requests
import adal
import json

'''
This is an example of how to request a token from AD.

All the variables below should never be committed to the repository.
Store and load them with a config.json file
'''
with open('config.json', 'r') as f:
    config = json.loads(f.read())

authorityHostUrl = config['authorityHostUrl']
tenant = config['tenant']
resource = config['clientId']
clientId = config['clientId']
clientSecret = config['clientSecret']

context = adal.AuthenticationContext(authorityHostUrl + '/' + tenant)
token = context.acquire_token_with_client_credentials(
    resource,
    clientId,
    clientSecret)

access_token = token['accessToken']
headers = {'Authorization': 'Bearer ' + access_token, 'Content-Type': 'application/json'}
data = json.dumps({"text": "hopefully this is the right data!"})

url = "https://dateml.dnvgl.com/predict"
# url = "http://localhost/status"

r = requests.post(url, headers=headers, data=data)
# JSON IPYTHON visualizer:
IPython.display.JSON(json.loads(r.text))
