#!/usr/bin/python 

import requests
import time
import config

time.sleep(10)
# replace URL 
requests.get(config.URL)
