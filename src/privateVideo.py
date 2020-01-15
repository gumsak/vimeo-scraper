#Video scraper for Vimeo (Get a public or private video)
#Git repo : https://github.com/gumsak/vimeo-scraper
"""
TODO: handle specific 'errors': file with same name already exists, download is 
interupted, etc
TODO: use python's naming conventions
TODO: implement video segments' download if we can't get the .mp4 file
TODO: set more solid regex search
TODO: implement whole albums/playlists download
TODO: check url validity, handle response status code, missing password, etc
TODO: GIT - merge this branch with master
"""
#import libs
from __future__ import print_function
import sys, os
import json
import re
import requests
from tqdm import tqdm

#Scrapy use: 
#https://docs.scrapy.org/en/latest/topics/dynamic-content.html
#https://docs.scrapy.org/en/latest/topics/developer-tools.html
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
import logging

import lxml.etree
import lxml.html

#import the config file to use confidential data
configPath = '..'
sys.path.append(os.path.abspath(configPath))

vimeoHome = 'https://vimeo.com'
vimeoDomain = 'vimeo.com'

videoUrl = ''
videoPassword = ''

videoTitle = ''
videoDataSource = ''

pathName = '../videos/'

videoIsPublic = True
isPlaylist = False

#current session's data
sessionToken = ''
sessionCookie = ''

#used to store the IDs corresponding of all the videos from a playlist
playlistIds = []

#get the arguments from the command line
#arg 1 = url, arg 2 = password
def getUserArgs():
    global videoUrl
    global videoPassword
    global videoIsPublic
    
    #user gave url & password
    if len(sys.argv) == 3:
        videoUrl = sys.argv[1]
        videoPassword = sys.argv[2]
        videoIsPublic = False
        print(sys.argv[1])
        
    #user gave url only
    elif len(sys.argv) == 2:
        videoUrl = sys.argv[1]
        print(videoUrl)
        
    #user gave wrong/no arguments
        #TODO: display help/correct parameters
    else:
        print("Input Error", file=sys.stderr)
        exit()

#print the logging informations in a file
def setLogOutput():
    
    configure_logging(install_root_handler=False)

    logging.basicConfig(
        filename='logs.log',
        format='%(levelname)s: %(message)s',
        level=logging.INFO
        )

#get the page's source code
def getPageSource(response):
    page = lxml.html.fromstring(response.body)
    #print(response.body)
    return page

#retrieve the token, cookie, etc, from the website; Needed to make a request
def getSessionData(webPage):
    global sessionToken
    global sessionCookie
    
    #print(webPage.body)
    
    """
    The vuid & the token are stored in different variables, depending if
    the link is for a playlist or for a single video
    """
    #if the link given is a playlist
    if isPlaylist:
        data = re.findall('bootstrap_data = {"viewer":(.+?}}})',
                          webPage.body.decode("utf-8"),
                          re.S)
        """
        add closing curly brackets at the end of the string to get a proper 
        json object
        """
        data[0] += '}}'
    #if it is a single video
    else:
        #find the part of the code that has the needed data
        data = re.findall('_extend\(window, (.+?)\);\n',
                          webPage.body.decode("utf-8"),
                          re.S)
    
    #print(data)
    
    #convert the str from the source to JSON
    dataJson = json.loads(data[0])
    
   
    #find the token and the 'vuid' in the json
    for key, val in dataJson.items():
        #in single video
        if key == 'ablincoln_config':
            sessionCookie = val.get('user', 'user_problem').get('vuid', 'vuid_problem')
           
        if key == 'vimeo':
            sessionToken = val.get('xsrft', 'token_problem')
                
        #in playlist
        if key == 'ablincolnConfig':
            sessionCookie = val.get('user', 'user_problem').get('vuid', 'vuid_problem')
                
        if key == 'xsrft':
            sessionToken = val    
            
    print('Token:', sessionToken)
    print('Vuid:', sessionCookie)
    

#enter the video's password in the appropriate field (FormRequest)
#https://doc.scrapy.org/en/latest/topics/request-response.html#using-formrequest-from-response-to-simulate-a-user-login
def enterPassword(response, func):
    
    return scrapy.FormRequest.from_response(
            response,
            meta={'dont_redirect': True},
            formid='pw_form',
            formdata={'password': videoPassword},
            callback=func)

#define the actions to take if the password is wrong
def handleWrongPassword():
    pass

#get the data of the video
def getVideoSpecs(response):
    global videoTitle
    global videoDataSource
    
    print('Getting video informations...')
    
    data = re.findall("window.vimeo.clip_page_config =(.+?);\n", 
                      response.body.decode("utf-8"), 
                      re.S)
        
    if data == []:
        exit('NO DATA FOUND')
    
    dataJson = json.loads(data[0])

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
    
    print('Initializing download...')

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
            f.write(data)
            
    t.close()
    #urllib.request.urlretrieve(url, videoTitle + extension)

#download all the videos from a playlist/album/showcase
def downloadPlaylist():
    
    
    pass

#check whether the user is trying to download a public or a private video to
#select the correct spider
def checkPublicOrPrivateVideo():
    
    print('This is a {} link'.format('public' if videoIsPublic else 'private'))
    
    if videoIsPublic:
        return PublicVideoSpider()
    else:
        return PrivateVideoSpider()

#check if the user provided a link to a playlist
def checkIfPlaylist(url):
    
    if re.search(vimeoDomain + r'\/showcase\/[0-9]', url) == None:
        return False
    return True

#retrieve the IDs of the videos in the playlist
def getPlaylistVideos(response):
    '''
    Sends a GET Request to the server, to retrieve a list of the videos of the
    playlist, or rather their IDs
    '''
    global playlistIds
    
    print(response)

    
    #regex to find the IDs in the source code of the page
    data = re.findall("unlisted_hash_map\":(.+?})", 
                      response.body.decode("utf-8"), 
                      re.S)
    
    dataJson = json.loads(data[0])
    
    for key, val in dataJson.items():
    
        playlistIds.append(key)
        
    print(playlistIds)

#start crawling the website with the spider
#TODO: set dynamic user-agent:
#--> list of agents: https://developers.whatismybrowser.com/useragents/explore
def startCrawling():
    
    global isPlaylist
    
    print('This is a playlist:', checkIfPlaylist(videoUrl))
    isPlaylist = checkIfPlaylist(videoUrl)

    currentSpider = checkPublicOrPrivateVideo()
    
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0'
        })

    process.crawl(currentSpider)
    process.start() # the script will block here until the crawling is finished
    
#spider used to parse a public video
class PublicVideoSpider(scrapy.Spider):
    
    def __init__(self):
    
        self.name = 'publicVimeoSpider'
        self.allowed_domains = [vimeoDomain]
        self.start_urls=[videoUrl]
        print("*** Public video: URL = " + videoUrl + " ***")

    def parse(self, response):
        getVideoSpecs(response)
        
        yield scrapy.Request(videoDataSource, callback = self.getVideo)
        
    def getVideo(self, response):
        getVideoSource(response)

#spider used to parse a private video
class PrivateVideoSpider(scrapy.Spider):
    
    def __init__(self):
        
        if isPlaylist:
            privateVidUrl = videoUrl
            self.download_delay = 2 # 2 sec delay between requests
        else:
            privateVidUrl = videoUrl + '/password'
        
        self.name = 'privateVimeoSpider'
        self.allowed_domains = [vimeoDomain]
        self.start_urls=[privateVidUrl]
    
        print("*** Private video: URL = " + videoUrl + " ***")

        self.handle_httpstatus_list = [401]
        
        #log level = ERROR, DEBUG, INFO, WARNING...
        self.custom_settings = {
            'HTTPERROR_ALLOWED_CODES': [401],
            'LOG_LEVEL': 'ERROR'
            }
    
    def parse(self, response):
        
        #get the web page's source code
        getPageSource(response)
        
        #get the session related data from the source code
        getSessionData(response)
        
        #form data to check video access password in Vimeo
        body = 'password={}&is_review=&is_file_transfer=&token={}'.format(
        videoPassword, sessionToken)
        
        #header of a request used to access a password protected video
        headers = {'Origin': 'https://vimeo.com',
               'Referer':self.start_urls[0],
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0',
               'Content-type':'application/x-www-form-urlencoded'}
            
        #make a 'POST' request with the video's credentials to access it
        yield scrapy.Request(self.start_urls[0],
                          method='POST', 
                          headers=headers,
                          body=body,
                          callback= self.getVideo)#,'Cookie':'vuid=' + sessionCookie
           
    #look for the video's data
    def getVideo(self, response):
        #print(response.body)
        getPlaylistVideos(response)
        #getVideoSpecs(response)   
        #yield scrapy.Request(videoDataSource, callback = self.downloadVideo)

    #download the video
    def downloadVideo(self, response):
        getVideoSource(response)
        
#retrieve the url/password to use       
getUserArgs()

#launch the crawler/start the process
startCrawling()