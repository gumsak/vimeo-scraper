#Video scraper for Vimeo (Get a public video)
#Git repo : https://github.com/gumsak/vimeo-scraper
"""
Todo: handle private videos
Todo: add download progression status
Todo: handle specific 'errors': file with same name already exists, download is 
interupted, etc
Todo: add command line arguments
Todo: use python's naming conventions
Todo: implement video segments' download if we can't get the .mp4 file
"""

# import libs
from __future__ import print_function
import sys
import json
import re
import urllib.request

import scrapy
from scrapy.crawler import CrawlerProcess

#Scrapy use: 
#https://docs.scrapy.org/en/latest/topics/dynamic-content.html
#https://docs.scrapy.org/en/latest/topics/developer-tools.html

vimeoHome = 'https://vimeo.com'
vimeoDomain = 'vimeo.com'

videoUrl = ''
videoPassword = ''

videoTitle = ''
videoDataSource = ''

#path of the downloaded files
downloadPath = '/videos'

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

#get the data of the video
def getVideoSpecs(response):
    global videoTitle
    global videoDataSource
    
    data = re.findall("window.vimeo.clip_page_config =(.+?);\n", response.body.decode("utf-8"), re.S)
    dataJson = json.loads(data[0])
    #print(dataJson)

    for key, val in dataJson.items():
    
        #get the video's title from the source code
        if key == "clip":
            videoTitle = val.get("title", "Title")
            #print(videoTitle)
        
        #get the video's data path from the source code    
        if key == "player":
            videoDataSource = val.get("config_url", "Problem With Url")
            #print(videoDataSource)

#retrieve the video from the sources
def getVideoSource(response):
    
    data = json.loads(response.body_as_unicode())
    
    for key, val in data.items():
        if key == "request":
            filesSource = val.get("files").get("progressive")
            
            videoUrl = getBestQualityVideo(filesSource)
            
            #some urls end with the '.mp4' extension but others will end up 
            #with characters that have to be removed to get a proper mp4 file 
            fileUrl = formatVideoSource(videoUrl, '.mp4')
            
            downloadVideo(fileUrl, '.mp4')

#remove end characters from the file's url
def formatVideoSource(url, extension):
    
    #index of the last occurrence of this extension type in the url
    index = url.rfind(extension)
    cleanUrl = url[0:index+5]
    
    print(">>>>>> " + cleanUrl + " <<<<<<")
    return cleanUrl

#look through the videos to find the one with the best quality
def getBestQualityVideo(videoList):
    
    bestQualityVideo = None
    quality = 0
    
    #look for the video with the biggest width resolution
    for video in videoList:
        for k, v in video.items():
            
            if k == "width":
                if int(v) > quality:
                    
                    quality = int(v)
                    bestQualityVideo = video.get("url")
                    
    #print(bestQualityVideo)
    return bestQualityVideo

#download file from url
def downloadVideo(url, extension):
    urllib.request.urlretrieve(url, videoTitle + extension)

#start crawling the website with the spider
def startCrawling():
    process = CrawlerProcess()#{
        #'FEED_FORMAT': 'XML',
        #'FEED_URI': 'output.html',
       # }

    process.crawl(VimeoSpider)
    process.start() # the script will block here until the crawling is finished


#define the spider
class VimeoSpider(scrapy.Spider):
    getUserArgs()
    
    name = 'vimeoSpider'
    allowed_domains = [vimeoDomain]
    start_urls=[videoUrl]
    print("*** " + videoUrl + " ***")

    def parse(self, response):
        getVideoSpecs(response)
        
        yield scrapy.Request(videoDataSource, callback = self.getVideo)
        
    def getVideo(self, response):
        getVideoSource(response)
        
startCrawling()