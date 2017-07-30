import requests
from bs4 import BeautifulSoup
import http.client
import argparse
import sys

parser = argparse.ArgumentParser()

parser.add_argument("-p", "--project", type=int, help="this is the project id")
parser.add_argument("-s", "--survey", type=int, help="this is the survey id")
args = parser.parse_args()

if len(sys.argv) < 2:
    parser.print_help()
    sys.exit(1)

print(args.project)



