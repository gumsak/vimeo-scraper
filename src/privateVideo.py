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
TODO: add Docstring to functions
"""
#import libs
from __future__ import print_function
import sys, os
import json
import re
import requests
from tqdm import tqdm
import webbrowser

#Scrapy use: 
#https://docs.scrapy.org/en/latest/topics/dynamic-content.html
#https://docs.scrapy.org/en/latest/topics/developer-tools.html
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.log import configure_logging
from scrapy.http.cookies import CookieJar
import logging

from requests_toolbelt import MultipartEncoder

import lxml.etree
import lxml.html

import segments_decoder

#TODO: set dynamic user-agent:
#--> list of agents: https://developers.whatismybrowser.com/useragents/explore
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:72.0) Gecko/20100101 Firefox/72.0'

"""delay between 2 requests. Set higher than 2 seconds to avoid sending the
requests in a faster than humanly possible fashion (avoid bot detection)"""
REQUESTS_DELAY = 4

#import the config file to use confidential data
configPath = '..'
sys.path.append(os.path.abspath(configPath))

VIMEO_HOME = 'https://vimeo.com'
vimeoDomain = 'vimeo.com'

videoUrl = ''
videoPassword = ''

videoTitle = ''
videoDataSource = ''

#path of the folder where the videos will be saved
pathName = '../videos/'

videoIsPublic = True
isPlaylist = False

#current session's data
sessionToken = ''
sessionCookie = ''

#id of the playlist to download
playlist_id = ''

#used to store the IDs corresponding of all the videos from a playlist
playlist_video_ids = []

#hashed password returned by the server when the the authentication in a 
#private showcase is successful
showcase_hashed_pass = ''

jwt_authorization = ''

#url to get the video's segments
url_segments = ''

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
    global jwt_authorization
    #print(webPage.text)
    
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
            
        if key == 'jwt':
            jwt_authorization = val
            
    print('Token:', sessionToken)
    print('Vuid:', sessionCookie)
    print('JWT AUTH:', jwt_authorization)

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
    print(response.text)
    
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
            print('*************** SOURCE MP4: ' + videoDataSource + ' *************************************')

def get_video_segments(url):
    """
    Retrieve the video & audio segments of the current video
    """
    web_page = requests.get(url)
    print(web_page.text)
    
    video_list = json.loads(url)
    
    best_quality_video = None
    best_quality_audio = None
    quality = 0
    
    video_segments_list = []
    audio_segments_list = []
    
    video_base_url = ''
    audio_base_url = ''

    #look for the segments with the best video resolution
    for video in video_list['video']:
        for k, v in video.items():
            
            if k == "width":
                if int(v) > quality:
                    
                    quality = int(v)
                    video_base_url = video.get("base_url")
                    video_segments_list.clear()
                    
                    #get the initial segment
                    video_segments_list.append(video.get("init_segment"))
                    
                    #get the rest of the segments
                    for segments in video.get("segments"):
                        for seg_k, seg_v in segments:
                            if seg_k =="url":
                                video_segments_list.append(seg_v)
            
    print(video_segments_list)
    
    quality = 0
    
    """look for the segments with the best audio quality
    ref: https://medium.com/@MicroPyramid/understanding-audio-quality-bit-rate-sample-rate-14286953d71f
    """
    for audio in video_list['audio']:
        for k, v in audio.items():
            
            if k == "bitrate":
                if int(v) > quality:
                    
                    quality = int(v)
                    audio_base_url = audio.get("base_url")
                    audio_segments_list.clear()
                    
                    #get the initial segment
                    audio_segments_list.append(audio.get("init_segment"))
                    
                    #get the rest of the segments
                    for segments in audio.get("segments"):
                        for seg_k, seg_v in segments:
                            if seg_k =="url":
                                audio_segments_list.append(seg_v)
    
    print(audio_segments_list)
    
    segments_url = re.findall('(https:\/\/.+?\d\/sep)',url_segments)[0]
    video_segments_url = segments_url + '/video/'
    audio_segments_url = segments_url

    #for segment in 

#retrieve the video from the sources
def getVideoSource(response):
    
    global url_segments
    
    print('Initializing download...')
    print(response.text)
    
    data = json.loads(response.body_as_unicode())
        
    url_segments = data['request']['files']['dash']['cdns']['akfire_interconnect_quic']['url']
    print('AKFIRE >>>>>>>>>>>>>>>>>' + url_segments)
    
    get_video_segments(url_segments)
    """
    for key, val in data.items():
        if key == "request":
            filesSource = val.get("files").get("progressive")
            
            videoUrl = getBestQualityVideo(filesSource)
            
            #some urls end with the '.mp4' extension but others will end up 
            #with characters that have to be removed to get a proper mp4 file 
            fileUrl = formatVideoSource(videoUrl, '.mp4')
            
            downloadVideo(fileUrl, '.mp4')
    """
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

def downloadPlaylist(url, extension):
    """download all the videos from a playlist/album/showcase"""

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
    global playlist_video_ids
    
    #list of the playlist' videos' ids
    playlist_video_ids = re.findall("\/{}\/videos\/(.\d+)".format(playlist_id)
                                , response)

    print(playlist_video_ids)
    
#start crawling the website with the spider
def startCrawling():
    
    global isPlaylist
    
    print('This is a playlist:', checkIfPlaylist(videoUrl))
    isPlaylist = checkIfPlaylist(videoUrl)

    currentSpider = checkPublicOrPrivateVideo()
    
    process = CrawlerProcess({
        'USER_AGENT': USER_AGENT
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
            self.download_delay = REQUESTS_DELAY#delay in seconds between requests
        else:
            privateVidUrl = videoUrl + '/password'
        
        self.name = 'privateVimeoSpider'
        self.allowed_domains = [vimeoDomain]
        self.start_urls=[privateVidUrl]
    
        print("*** Private video: URL = " + videoUrl + " ***")

        self.handle_httpstatus_list = [401]
        self.HTTPERROR_ALLOWED_CODES = [401]
        
        self.COOKIES_DEBUG = True
        
        #log level = ERROR, DEBUG, INFO, WARNING...
        self.custom_settings = {
            'HTTPERROR_ALLOWED_CODES': [401],
            'LOG_LEVEL': 'ERROR'
            }
        
    def parse(self, response):
               
        global playlist_id
        
        #delimiter used to separate the form data
        boundary = "---------------------------89844361214769076511231454046"
        
        #get the id of the playlist/album/showcase
        playlist_id = re.findall("\/showcase\/(.\d+)", self.start_urls[0])[0]

        #get the referer url (ex: /showcase/123456)
        referer_url = re.findall("(\/showcase.+?\d+)", self.start_urls[0])
        
        #get the web page's source code
        #getPageSource(response)
        
        #get the session related data from the source code
        getSessionData(response)

        #form data to check video access password in Vimeo
        body = '{}\nContent-Disposition: form-data; name="password"\n\n{}\n{}\nContent-Disposition: form-data; name="token"\n\n{}\n{}\nContent-Disposition: form-data; name="referer_url"\n\n{}\n{}--\n'.format(
        '--'+boundary, videoPassword, '--'+boundary, sessionToken, 
        '--'+boundary, referer_url[0],'--' + boundary)
                
        '''             
        #header of a request used to access a password protected playlist
        headers = {'Origin':VIMEO_HOME,
               'Referer':self.start_urls[0],
               'User-Agent':USER_AGENT,
               'Cookie':'vuid='+sessionCookie,
               'Content-Type':'multipart/form-data; charset=utf-8; boundary=' + boundary,
               'Accept': '*/*',
               'DNT': '1',
               'Accept-Language': 'fr,fr-FR;q=0.8,en-US;q=0.5,en;q=0.3',
               'Accept-Encoding': 'gzip, deflate, br'
               }
        '''
        m = MultipartEncoder(fields={
            'password':videoPassword,
            'token':sessionToken,
            'referer_url':referer_url[0]})
        
        body = m.to_string()

        cookie = 'vuid=' + sessionCookie

        headers = {'Origin':VIMEO_HOME,
               'Referer':self.start_urls[0],
               'User-Agent':USER_AGENT,
               'Cookie':cookie,
               'Content-Type':m.content_type
               }
        
        print(type(body))
        print(body.decode("utf-8"))
        print(type(headers))
        print(headers)
        print(playlist_id)
                
        #send request for authentication
        auth_request = scrapy.Request(self.start_urls[0] + '/auth',
                          method='POST', 
                          headers=headers,
                          body=body.decode("utf-8"),
                          meta={'dont_merge_cookies': True},
                          callback= self.getVideo)
        
        return auth_request
    
    def parse1(self, response):
        
        #get the web page's source code
        getPageSource(response)
        
        #get the session related data from the source code
        getSessionData(response)
        
        #form data to check video access password in Vimeo
        body = 'password={}&is_review=&is_file_transfer=&token={}'.format(
        videoPassword, sessionToken)
        
        #header of a request used to access a password protected video
        headers = {'Origin': VIMEO_HOME,
               'Referer':self.start_urls[0],
               'User-Agent': USER_AGENT,
               'Content-type':'application/x-www-form-urlencoded'}
            
        #make a 'POST' request with the video's credentials to access it
        yield scrapy.Request(self.start_urls[0],
                          method='POST', 
                          headers=headers,
                          body=body,
                          callback= self.getVideo)#,'Cookie':'vuid=' + sessionCookie
           
    #look for the video's data
    
    #make a request to get the page showing the videos from the playlist
    def access_showcase():
        
        page = 1
        per_page = 12
        
        album_url = 'https://api.vimeo.com/albums/{}/videos?page={}&sort=manual&fields=description%2Cduration%2Cis_free%2Clive%2Cname%2Cpictures.sizes.link%2Cpictures.sizes.width%2Cpictures.uri%2Cprivacy.download%2Cprivacy.view%2Ctype%2Curi%2Cuser.link%2Cuser.name%2Cuser.pictures.sizes.link%2Cuser.pictures.sizes.width%2Cuser.uri&per_page=12&filter=&_hashed_pass={}'.format(playlist_id, page, per_page, showcase_hashed_pass)
        
        #Accept: application/vnd.vimeo.video;version=3.4.1
        headers = {'Origin':VIMEO_HOME,
                   'Referer':VIMEO_HOME,
                   'User-Agent':USER_AGENT,
                   'Content-Type':'application/json',
                   'Authorization': 'jwt ' + jwt_authorization
                   }
        """
        #make a 'GET' request with the playlist's data
        yield scrapy.Request(album_url,
                          method='GET', 
                          headers=headers,
                          callback= self.get_playlist_videos)
        """
        
    def getVideo(self, response):
        """Access the playlist"""
    
        global showcase_hashed_pass
        
        #print(response.body)
       
        json_from_response = json.loads(response.body_as_unicode())
        showcase_hashed_pass = json_from_response["hashed_pass"]
        print(showcase_hashed_pass)
        
        #scrapy.utils.response.open_in_browser(response)
        print(response.request.url)
        
        page = 1
        per_page = 12
        
        album_url = 'https://api.vimeo.com/albums/{}/videos?page={}&sort=manual&fields=description%2Cduration%2Cis_free%2Clive%2Cname%2Cpictures.sizes.link%2Cpictures.sizes.width%2Cpictures.uri%2Cprivacy.download%2Cprivacy.view%2Ctype%2Curi%2Cuser.link%2Cuser.name%2Cuser.pictures.sizes.link%2Cuser.pictures.sizes.width%2Cuser.uri&per_page={}&filter=&_hashed_pass={}'.format(playlist_id, page, per_page, showcase_hashed_pass)
        
        #Accept: application/vnd.vimeo.video;version=3.4.1
        headers = {'Origin':VIMEO_HOME,
                   'Referer':VIMEO_HOME,
                   'User-Agent':USER_AGENT,
                   'Content-Type':'application/json',
                   'Authorization': 'jwt ' + jwt_authorization
                   }

        #make a 'GET' request with the playlist's data
        yield scrapy.Request(album_url,
                          method='GET', 
                          headers=headers,
                          callback= self.get_playlist_videos,
                          meta={'dont_merge_cookies': True}
                          )
        
        #getPlaylistVideos(response)
        #getVideoSpecs(response)   
        #yield scrapy.Request(videoDataSource, callback = self.downloadVideo)
        #pass
        
    #retrieve the videos' ids from the playlist, then start the downloading process
    def get_playlist_videos(self, response):
        """Retrieve the videos' ids from the playlist, then start the 
        downloading process for each video"""
        
        #print(response.text)

        getPlaylistVideos(response.text)
        
        cookie = 'vuid={}; {}_albumpassword={}; _abexps=%7B%22982%22%3A%22variant%22%7D; continuous_play_v3=1'.format(sessionCookie, playlist_id, showcase_hashed_pass)
        
        #loop through the videos to get their ids
        for video_id in playlist_video_ids:
        
        #video_id = playlist_video_ids[0]
        
            url = self.start_urls[0] + '/video/' + video_id
        
            #header of a request used to access a protected video
            headers = {'Origin':VIMEO_HOME,
                       'Referer':self.start_urls[0],
                       'User-Agent':USER_AGENT,
                       'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                       'Upgrade-Insecure-Requests':'1',
                       'Cookie':cookie
                       }

            print('++++++++++++++++++++ DOWNLOADING VIDEO: ' + video_id + 
                  '++++++++++++++++++')
            #print(cookie)
            #print(url)
            #print(headers)
            
            #make a 'POST' request with the video's credentials to access it
            yield scrapy.Request(url,
                                 method='GET', 
                                 headers=headers,
                                 callback= self.downloadVideo,#,meta={'dont_redirect':True}
                                 dont_filter=True,
                                 meta={'dont_merge_cookies': True}
                                 )
    
    def post_auth(self, response):
       
        getVideoSpecs(response)
        
        yield scrapy.Request(videoDataSource, callback = self.getVideo)
        
        getVideoSource(response)
        
        print(response.body)
        
        referer_url = re.findall("(\/showcase.+?\d+)", self.start_urls[0])
        
        m = MultipartEncoder(fields={
            'password':videoPassword,
            'token':sessionToken,
            'referer_url':referer_url[0]})
        
        body = m.to_string()

        headers = {'Origin':VIMEO_HOME,
               'Referer':self.start_urls[0],
               'User-Agent':USER_AGENT,
               'Content-Type':m.content_type
               }
        
        yield scrapy.Request(self.start_urls[0] + '/auth',
                          method='GET', 
                          headers=headers,
                          body=body,
                          callback= self.getVideo)
    
    #download the video
    def downloadVideo(self, response):
        
        #print(response.text)
        
        if response.status != 302:
            getVideoSpecs(response)##
            yield scrapy.Request(videoDataSource, callback = self.start_download)
        else:
            print('ERROR >>> 302 <<<, GETTING REDIRECTED...')
            print(response.url)
            yield scrapy.Request(response.urljoin(response.url), 
                                 callback= self.downloadVideo,
                                 meta={'dont_merge_cookies': True})
        
    def start_download(self, response):
        getVideoSource(response)
        
#retrieve the url/password to use       
getUserArgs()

#launch the crawler/start the process
startCrawling()