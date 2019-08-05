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
# python src/scrape_reviews.py  data/scraped_gw_reviews.csv 5

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
parser.add_argument("sleep_time")
args = parser.parse_args()
save_path = args.save_path
sleep_time = float(args.sleep_time)

def main():

    # access the Germanwings first review page
    sys.stdout.write("Accessing the Germanwings review page.\n")
    sys.stdout.flush()
    gw_reviews_url = sneaky_request("https://www.airlinequality.com/airline-reviews/germanwings/")

    # check that our status is okay, if not exit the script
    if gw_reviews_url.reason != "OK":
        sys.stdout.write("Status is not okay, exiting script.")
        sys.stdout.flush()
        sys.exit()

    sys.stdout.write("Accessed URL: {} \nStatus: {}\n".format(gw_reviews_url.geturl(), gw_reviews_url.reason))
    sys.stdout.flush()

    # Use BeautifulSoup to explore and scrape the pages for the relevant info.

    gw_reviews = BeautifulSoup(gw_reviews_url.read(), features = "lxml")

    # We need to traverse all of the pages in order to extract all of the reviews;
    # this means opening each subsequent page and extracting each review.

    # The following while loop iterates over each subsequent review page,
    # terminating when there are no further pages to scrape. The airline review
    # information is stored in reviews, to be parsed after extracting
    # all of the information.

    # create the initial list and condition to keep scraping
    reviews = []
    keep_going = True

    sys.stdout.write("Scraping all review pages, this will take some time depending \
on the input sleep time.\n")
    sys.stdout.flush()

    while keep_going:

        # store the customer reviews in a list for later parsing
        if len(reviews) == 0:
            # if it is the first page, create the list
            reviews = gw_reviews.find_all("article", {"itemprop" : "review"})
        else:
            # concatenate the next pages reviews
            for review in gw_reviews.find_all("article", {"itemprop" : "review"}):
                reviews.append(review)

        # find the next page tag, use it to construct the next page to access
        # if it is the last page, end the loop
        try:
            next_page = gw_reviews.find("a", string = ">>")["href"]
            next_page_url = "https://www.airlinequality.com" + next_page
        except:
            keep_going = False

        # open the next page, but wait some seconds to be polite
        # and not overload the server
        time.sleep(sleep_time)
        gw_reviews_url = sneaky_request(next_page_url)
        gw_reviews = BeautifulSoup(gw_reviews_url.read(), features = "lxml")

    # Iterate through the reviews, building lists of the required information.

    # Note that this could be done in parallel using a library such as joblib,
    # but the dataset is so small that there is no need to implement it.

    # build a dictionary structure for easily working with, and to convert to a
    # pandas dataframe later
    parsed_reviews = {
        "title" : [],
        "review_value" : [],
        "n_user_reviews" : [],
        "reviewer_name" : [],
        "reviewer_country" : [],
        "date_of_review" : [],
        "review_text" : [],
        "aircraft" :[],
        "traveller_type" : [],
        "seat_type" : [],
        "route" : [],
        "date_flown" : [],
        "seat_comfort_rating" : [],
        "cabin_staff_service_rating" : [],
        "food_and_beverages_rating" : [],
        "inflight_entertainment_rating" : [],
        "ground_service_rating" : [],
        "value_for_money_rating" : [],
        "recommendation" : []
    }

    # iterate through all reviews, extracting information from each
    # and storing in the parsed_reviews dict
    sys.stdout.write("Parsing reviews\n")
    sys.stdout.flush()

    for review in reviews:

        # extract review title
        review_title = review.find("h2", {"class" : "text_header"})
        parsed_reviews["title"].append(safe_extract(review_title))

        # extract review value out of 10
        review_value = review.find("span", {"itemprop" : "ratingValue"})

        # if there is no value out of 10, enter None instead using `safe_extract`
        parsed_reviews["review_value"].append(safe_extract(review_value))

        # extract number of reviews by the reviewer
        n_reviews = review.find("span", {"class" : "userStatusReviewCount"})
        parsed_reviews["n_user_reviews"].append(safe_extract(n_reviews))

        # extract the reviewer
        reviewer_name = review.find("span", {"itemprop" : "name"})
        parsed_reviews["reviewer_name"].append(safe_extract(reviewer_name))

        # extract the country of the reviewer
        reviewer_country = review.find("h3", {"class" : "text_sub_header userStatusWrapper"})
        parsed_reviews["reviewer_country"].append(safe_extract(reviewer_country))

        # extract the date of the review
        date_of_review = review.find("time", {"itemprop" : "datePublished"})
        parsed_reviews["date_of_review"].append(safe_extract(date_of_review))

        # extract the review text
        review_text = review.find("div", {"class" : "text_content"})
        parsed_reviews["review_text"].append(safe_extract(review_text))

        # extract the aircraft
        # there are multiple td with class = "review-value"
        # so we need to find the sibling header for aircraft then find it's sibling
        # in order to find the aircraft type.  Use sibling_extract for this
        aircraft = review.find("td", {"class" : "review-rating-header aircraft"})
        aircraft_value = sibling_extract(aircraft)
        parsed_reviews["aircraft"].append(aircraft_value)

        # extract the type of traveller
        traveller_type = review.find("td", {"class" : "review-rating-header type_of_traveller"})
        traveller_type_value = sibling_extract(traveller_type)
        parsed_reviews["traveller_type"].append(traveller_type_value)

        # extract seat type
        seat_type = review.find("td", {"class" : "review-rating-header cabin_flown"})
        seat_type_value = sibling_extract(seat_type)
        parsed_reviews["seat_type"].append(seat_type_value)

        # extract the route
        route = review.find("td", {"class" : "review-rating-header route"})
        route_value = sibling_extract(route)
        parsed_reviews["route"].append(route_value)

        # extract the date flown
        date_flown = review.find("td", {"class" : "review-rating-header date_flown"})
        date_flown_value = sibling_extract(date_flown)
        parsed_reviews["date_flown"].append(date_flown_value)

        # extract the seat comfort rating out of 5
        # need to find the sibling in order to narrow down the number of stars for
        # seat comfort or other ratings.  use star_extract to do this for us
        seat_comfort_rating = review.find("td", {"class" : "review-rating-header seat_comfort"})
        parsed_reviews["seat_comfort_rating"].append(star_extract(seat_comfort_rating))

        # extract the cabin staff service rating out of 5
        cabin_staff_service_rating = review.find("td", {"class" : "review-rating-header cabin_staff_service"})
        parsed_reviews["cabin_staff_service_rating"].append(star_extract(cabin_staff_service_rating))

        # extract the food and beverages rating out of 5
        food_and_beverages_rating = review.find("td", {"class" : "review-rating-header food_and_beverages"})
        parsed_reviews["food_and_beverages_rating"].append(star_extract(food_and_beverages_rating))

        # extract the inflight entertainment rating out of 5
        inflight_entertainment_rating = review.find("td", {"class" : "review-rating-header inflight_entertainment"})
        parsed_reviews["inflight_entertainment_rating"].append(star_extract(inflight_entertainment_rating))

        # extract the ground service rating out of 5
        ground_service_rating = review.find("td", {"class" : "review-rating-header ground_service"})
        parsed_reviews["ground_service_rating"].append(star_extract(ground_service_rating))

        # extract the value for money rating out of 5
        value_for_money_rating = review.find("td", {"class" : "review-rating-header value_for_money"})
        parsed_reviews["value_for_money_rating"].append(star_extract(value_for_money_rating))

        # extract if the review recommended Germanwings or not
        recommendation = review.find("td", {"class" : "review-rating-header recommended"}).find_next("td")
        parsed_reviews["recommendation"].append(recommendation.text)

        # Now that all information is parsed, convert to a pandas dataframe
        # and save as a csv.

    parsed_reviews_df = pd.DataFrame(parsed_reviews)

    sys.stdout.write("Saving csv to {}\n".format(save_path))
    sys.stdout.flush()

    parsed_reviews_df.to_csv(save_path, index = False)

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
        sys.stdout.write("Error code: ", error.code)
        sys.stdout.write("The reason for the exception:", error.reason)
        sys.stdout.flush()

    return open_url

def safe_extract(extracted_tag, replacement_value = None):
    """
    safe_extract is used to extract text from html tags when sometimes the tag doesn't exist.
    Instead of throwing an error, it provides a defined replacement value

    Args:
        extracted_tag (Tag) : BeautifulSoup html tag containing the desired text
        replacement_value (int, bool, str, dbl...) : if the tag doesn't exist, what
                                                     should it be replaced with?

    Return:
        the extracted text if it exists, if not then the replacement value
    """
    try:
        value = extracted_tag.text
    except:
        value = replacement_value

    return value

def sibling_extract(extracted_tag, next_tag = "td", replacement_value = None):
    """
    sibling_extract is used to extract text from a html tag's sibling when sometimes the tag doesn't exist.
    Instead of throwing an error, it provides a defined replacement value

    Args:
        extracted_tag (Tag) : BeautifulSoup html tag containing the desired text
        next_tag (str) : next tag type to find
        replacement_value (int, bool, str, dbl...) : if the tag doesn't exist, what
                                                     should it be replaced with?

    Return:
        the extracted text if it exists, if not then the replacement value
    """
    try:
        # using find_next to find the sibling with the specified tag
        value = extracted_tag.find_next(next_tag).text
    except:
        value = None

    return value

def star_extract(extracted_tag, next_tag = "td", replacement_value = None):
    """
    star_extract is used to extract the number of rated stars from a html tag.
    When the rating doesn't exist, instead of throwing an error
    it provides a defined replacement value

    Args:
        extracted_tag (Tag) : BeautifulSoup html tag containing the desired star ratings
        next_tag (str) : next tag type to find
        replacement_value (int, bool, str, dbl...) : if the tag doesn't exist, what
                                                     should it be replaced with?

    Return:
        the extracted number of stars if it exists, if not then the replacement value
    """
    try:
        # find the number of stars that have class = "star fill" representing
        # the number of rated stars.
        #
        # For example, a 4 star rating will have 4 class = "star fill" and
        # one class = "star"
        #
        # the sibling tag will need to be found as well since
        # the class value is not unique for the number of stars
        filled_star_tags = extracted_tag.find_next(next_tag).find_all("span", {"class" : "star fill"})

        # the number of filled in star tags is the rating
        value = len(filled_star_tags)

    except:
        value = None

    return value

# call main function
if __name__ == "__main__":
    main()
