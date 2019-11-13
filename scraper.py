# Porjet scraper Vimeo

# import libs
import scrapy

vimeoHome = 'https://vimeo.com/'

# class to represent a video available online / this is the spider
class Video(scrapy.Spider):
    name = "vimeo_spider"
    start_urls = ['https://vimeo.com/32876686']
    #constructor
   #def __init__(self, vidName, url):
        # name of the video
       # self.vidName = vidName
        # URL of the video
      #  self.url = url

	#parse the video's url
    def parse(self, response):
        print(response.text)

# create one object to retrieve a video
#vidTest = Video("vid1","https://vimeo.com/32876686")

#vidTest.parse
    
# GET from the given address
#response = requests.get("https://www.google.fr/")

#print(response.status_code)

#ploads = {'things':2, 'total':25}

#r = requests.get('https://httpbin.org/get', params = ploads)

#print(r.text)
#print(r.url)

# Init the crawler

#print(response.text)
