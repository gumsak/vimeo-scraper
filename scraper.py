# Porjet scraper Vimeo

# import libs
import requests
import scrapy

# class to represent a video available online
class Video:
    #constructor
    def __init__(self, name, url):
        # name of the video
        self.name = name
        # URL of the video
        self.url = url

    def setName(self):
        

# create one object to retrieve a video
vid1 = Video("et","at")

print(vid1.url)
    
# GET from the given address
#response = requests.get("https://www.google.fr/")

#print(response.status_code)

#ploads = {'things':2, 'total':25}

#r = requests.get('https://httpbin.org/get', params = ploads)

#print(r.text)
#print(r.url)

# Init the crawler



#print(response.text)
