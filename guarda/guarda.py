#!/usr/bin/python 

import requests
import time

# requests.get('https://127.0.0.1/announce_all')
time.sleep(10)
# replace URL 
requests.get('https://exafs.cesnet.cz/announce_all')
