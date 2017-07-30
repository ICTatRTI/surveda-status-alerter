import requests
from bs4 import BeautifulSoup
import http.client
import argparse
import sys
import os

parser = argparse.ArgumentParser()

parser.add_argument("-p", "--project", type=int, help="this is the project id")
parser.add_argument("-s", "--survey", type=int, help="this is the survey id")
args = parser.parse_args()

if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

SURVEDA_URL = os.environ.get("SURVEDA_URL")
os.environ.get("SURVEDA_USER")
os.environ.get("SURVEDA_PASS")
os.environ.get("SPARKPOST_KEY")
os.environ.get("SPARKPOST_TEMPLATE_ID")
os.environ.get("REDIS_URL")
os.environ.get("REDIS_PASS")
os.environ.get("REDIS_PORT")


page = requests.get(SURVEDA_URL+'/sessions/new')
soup = BeautifulSoup(page.content, 'html.parser')



