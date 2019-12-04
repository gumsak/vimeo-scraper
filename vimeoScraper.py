#Video scraper for Vimeo (Get a public video)

# import libs
from __future__ import print_function
import sys
import json
import re

#Scrapy use: 
#https://docs.scrapy.org/en/latest/topics/dynamic-content.html
#https://docs.scrapy.org/en/latest/topics/developer-tools.html
import scrapy
from scrapy.crawler import CrawlerProcess
 
vimeoHome = 'https://vimeo.com'
vimeoDomain = 'vimeo.com'
videoUrl = ''
videoPassword = ''

videoTitle = ''

#get the arguments from the command line
#arg 1 = url, arg 2 = password
def getUserArgs():
    global videoUrl
    global videoPassword
        
    #user gave url & password
    if len(sys.argv) == 3:
        videoUrl = sys.argv[1]
        videoPassword = sys.argv[2]
        print(sys.argv[1])
        
    #user gave url only
    elif len(sys.argv) == 2:
        videoUrl = sys.argv[1]
        print(videoUrl)
        
    #user gave wrong/no arguments
    else:
        print("Input Error", file=sys.stderr)
        exit()

#get the title of the video
def getVideoSpecs(response):
    global videoTitle

    data = re.findall("window.vimeo.clip_page_config =(.+?);\n", response.body.decode("utf-8"), re.S)
    dataJson = json.loads(data[0])
    print(dataJson)

    for key, val in dataJson.items():
        if key == "clip":
            print(val.get("title", "Title"))
            
        if key == "player":
            print(val.get("config_url", "Problem With Url"))

#define the spider
class VimeoSpider(scrapy.Spider):
    getUserArgs()
    name = 'vimeoSpider'
    allowed_domains = [vimeoDomain]
    start_urls=[videoUrl]
    print("*** " + videoUrl + " ***")

    def parse(self, response):
        #print(response.text)
        getVideoSpecs(response)

#start crawling the website with the spider
def startCrawling():
    process = CrawlerProcess({
        'FEED_FORMAT': 'XML',
        'FEED_URI': 'output.html',
        })

    process.crawl(VimeoSpider)
    process.start() # the script will block here until the crawling is finished

startCrawling()