#
# scrape_reviews.py
#
# @author: Evan Yathon
#
# August 2019
#
# scrape_reviews is used to grab information from airlinequality.com.  It is
# currently optimized for Germanwings, but can be easily extended to other
# airlines on the same website.
#
# sample usage
# python src/scrape_reviews.py  data/scraped_gw_reviews.csv

# loading packages

# utils
import pandas as pd
import time
import argparse
import sys

# scraping
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from bs4 import BeautifulSoup

# load argument for save path
parser = argparse.ArgumentParser()
parser.add_argument("save_path")
args = parser.parse_args()
save_path = args.save_path

def main():

    # access the Germanwings first review page
    print("Accessing the Germanwings review page.")
    gw_reviews_url = sneaky_request("https://www.airlinequality.com/airline-reviews/germanwings/")

    # check that our status is okay, if not exit the script
    if gw_reviews_url.reason != "OK":
        print("Status is not okay, exiting script.")
        sys.exit()

    print("Accessed URL: %s \nStatus: %s".format(gw_reviews_url.geturl(), gw_reviews_url.reason))

    # Use BeautifulSoup to explore and scrape the pages for the relevant info.

    gw_reviews = BeautifulSoup(gw_reviews_url.read())

    # We need to traverse all of the pages in order to extract all of the reviews;
    # this means opening each subsequent page and extracting each review.

    # The following while loop iterates over each subsequent review page,
    # terminating when there are no further pages to scrape. The airline review
    # information is stored in reviews, to be parsed after extracting
    # all of the information.



def sneaky_request(url):
    """
    sneaky_request is a function designed to get around some pages blocking web scraping.
    It uses a different User-Agent than the default `python urllib/3.X.X`

    Args:
        url (str) : url of the website desired to be scraped

    Return:
        open_url (HTTPResponse) : the HTTP response of the input URL
    """

    #`airlinequality.com` had a blocker for the default `urllib` agent, so this workaround was found in order to correctly scrape the reviews.
    # Source:
    # https://stackoverflow.com/questions/16627227/http-error-403-in-python-3-web-scraping
    #
    # Enable some default error handling in case the site cannot be accessed, and tell us why.
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        open_url = urlopen(req)
    except HTTPError as error:
        print("Error code: ", error.code)
        print("The reason for the exception:", error.reason)

    return open_url

# call main function
if __name__ == "__main__":
    main()
