#Video scraper for Vimeo (Get a private video)
#Todo: same as vimeoScraper.py if any  

# import libs
from __future__ import print_function
import sys, os
import json
import re
#import urllib.request
import requests
from tqdm import tqdm

#Scrapy use: 
#https://docs.scrapy.org/en/latest/topics/dynamic-content.html
#https://docs.scrapy.org/en/latest/topics/developer-tools.html
import scrapy
from scrapy.crawler import CrawlerProcess

#import the config file to use confidential data
configPath = '..'
sys.path.append(os.path.abspath(configPath))
import config

vimeoHome = 'https://vimeo.com'
vimeoDomain = 'vimeo.com'

videoUrl = ''
videoPassword = ''

videoTitle = ''
videoDataSource = ''

pathName = '../videos/'

#vimeo password field
vimeoPassField = ''

#url & password of the test videosS
videoUrl = config.url_video_test

videoPassword = config.pass_private_vid
privateVideo = config.url_private_vid
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

#get the page's source code
def getPageSource(response):
    print(response.text)

#retrieve the token necessary to make the POST request 
def getToken():
    pass

#make a POST request on a website with the chosen
def makePostRequest():
    pass

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
#progress bar implementation : https://stackoverflow.com/a/37573701
def downloadVideo(url, extension):
    
    fileName = pathName + videoTitle + extension
    
    #download the file
    file = requests.get(url, stream = True)
    
    #get the size in bytes of the received body
    fileSize = int(file.headers.get('content-length', 0))
    blockSize = 1024
    
    #initialize the progress bar
    t = tqdm(total = fileSize, unit = 'iB', unit_scale = True)
    
    #create the directory where the downloaded files will be saved 
    try:
        os.makedirs(os.path.dirname(pathName), exist_ok=False)
    except FileExistsError:
        pass

    #save it
    with open(fileName, 'wb') as f:
        for data in file.iter_content(blockSize):
            t.update(len(data))
            #f.write(file.content)
            f.write(data)
            
    t.close()
    #urllib.request.urlretrieve(url, videoTitle + extension)

'''
def createVideoDirectory(pathName):
    
    os.makedirs(os.path.dirname(pathName), exist_ok=False)
    with open(filename, "w") as f:
        f.write("FOOBAR")
'''
#start crawling the website with the spider
def startCrawling():
    process = CrawlerProcess()#{
        #'FEED_FORMAT': 'XML',
        #'FEED_URI': 'output.html',
       # }

    #process.crawl(VimeoSpider)
    process.crawl(PrivateVidSpider)
    process.start() # the script will block here until the crawling is finished


#define the spider
class VimeoSpider(scrapy.Spider):
    #getUserArgs()
    
    name = 'vimeoSpider'
    allowed_domains = [vimeoDomain]
    start_urls=[videoUrl]
    print("*** " + videoUrl + " ***")

    def parse(self, response):
        getVideoSpecs(response)
        
        yield scrapy.Request(videoDataSource, callback = self.getVideo)
        
    def getVideo(self, response):
        getVideoSource(response)
        
class PrivateVidSpider(scrapy.Spider):
    
    name = 'privateSpider'
    allowed_domains = [vimeoDomain]
    start_urls=[privateVideo]
    
    def parse(self, response):
        #getPageSource(response)
        
        yield print(str(response.request))
    
startCrawling()