# Porjet scraper Vimeo

# import lib requests
import requests

# get from the given address
response = requests.get("https://www.google.fr/")

print(response.status_code)

ploads = {'things':2, 'total':25}

r = requests.get('https://httpbin.org/get', params = ploads)

print(r.text)
print(r.url)

#print(response.text)