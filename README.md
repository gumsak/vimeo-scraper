# vimeo-scraper
### Web scraper made to retrieve videos from Vimeo -V.0.9

##### Implemented functions: #####

- creates a destination folder named ***'videos'*** for the downloaded videos (goes up one directory and create it, i.e *'../videos/'*) 

- download a single video -- public or private

- download a whole playlist (showcase) -- public or private

##### Libraries used: #####
```
scrapy
ffmpeg
ffmpy
requests
requests_toolbelt
tqdm
multiple ffmpeg codecs
```

#### How to use: ####

Make sure you have Python3 (tested with 3.7.3 on Ubuntu) and the libraries used in the program, then in the terminal type:

   `python3 vimeo_scraper.py url_of_the_video`
   
   If the video or playlist is password protected, just put the password after the URL: 
   
   `python3 vimeo_scraper.py url_of_the_video password`
      
#### TODO: ####

- [ ] Handle disk space use
- [ ] Show download progress
- [ ] Add pause/stop functions
- [ ] Multiplatform / OS / python versions tests
