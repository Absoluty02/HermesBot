import requests

request = requests.get("youtube.com")
if request.status_code == 200:
    print("ciao")
else:
    print("no")