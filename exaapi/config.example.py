"""
Example of configuration file

Add your log settings and rename to config.py
"""

LOG_FILE = "/var/log/exafs/exa_api.log"
LOG_FORMAT = "%(asctime)s:  %(message)s"


# rabbit mq
# note - rabbit mq must be enabled in main app config
# credentials and queue must be set here for the same values
EXA_API_RABBIT_HOST = "localhost"
EXA_API_RABBIT_PORT = "5672"
EXA_API_RABBIT_PASS = "mysecurepassword"
EXA_API_RABBIT_USER = "myexaapiuser"
EXA_API_RABBIT_VHOST = "/"
EXA_API_RABBIT_QUEUE = "my_exa_api_queue"
