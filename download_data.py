from stravalib.client import Client
import webbrowser
import yaml
from TCPServerWithReusableAddress import TCPServerWithReusableAddress
from HandlerWithAuth import HandlerWithAuth

with open("config.yml", 'r') as keys_file:
    secret_keys = yaml.safe_load(keys_file)

client = Client()
authorize_url = client.authorization_url(
    client_id=secret_keys['client_id'], 
    redirect_uri='http://127.0.0.1:5000/authorized',
    # Change to None if you don't want private activities included
    scope='activity:read_all'
)

# Have the user click the authorization URL, a 'code' param will be added to the redirect_uri
webbrowser.open(authorize_url)

with TCPServerWithReusableAddress(("127.0.0.1", 5000), HandlerWithAuth, client, secret_keys) as httpd:
    print("serving at port", 5000)
    httpd.handle_request()
    print("shutting down server")

