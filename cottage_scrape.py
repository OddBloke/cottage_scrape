import argparse
import logging
import re
import sys

import requests
from BeautifulSoup import BeautifulSoup


BASE_URL = "/england?adult=2&child=0&infant=0&pets=0&partyprofile=1&nights={nights}&start={start_date}&sortorder=4&trvlperiod=1"
FULL_COTTAGE_URL = 'http://www.cottages4you.co.uk{}'


def _get(url):
    return requests.get(FULL_COTTAGE_URL.format(url))


def get_property_details(property_element):
    prop_name = property_element.find('a')['href']
    price_span = property_element.find(attrs={'class': 'rst_basePrice'})
    now_price = price_span.find(attrs={'class': 'rst_spnNowPrice'})
    price_text = ''
    if now_price:
        price_text = now_price.text
    else:
        price_text = price_span.text
    match = re.search(r'[0-9]{3}.[0-9]{2}', price_text)
    return prop_name, float(match.group())


def scrape_page(url):
    logging.debug('Scraping {}...'.format(url))
    response = _get(url)
    soup = BeautifulSoup(response.content)

    properties = soup.findAll(attrs={'class': 'rst_propertyInfo'})
    prop_prices = {}
    for prop in properties:
        prop_name, price = get_property_details(prop)
        prop_prices[prop_name] = price
    pagination = soup.findAll('a', attrs={'class': 'PaginationLink'})
    next_url = None
    for pagination_link in pagination:
        if 'next' in pagination_link.text:
            next_url = pagination_link['href']
    return prop_prices, next_url


def scrape_pages(start_date, nights):
    prices = {}
    next_url = BASE_URL.format(start_date=start_date, nights=nights)
    while next_url is not None:
        price_dict, next_url = scrape_page(next_url)
        for cottage_url, price in price_dict.items():
            yield cottage_url, price


def filter_cottages(start_date, nights, price_point=None,
                    required_description_strings=[]):
    for cottage_url, price in scrape_pages(start_date, nights):
        if price_point and price > price_point:
            continue
        if required_description_strings:
            response = _get(cottage_url)
            soup = BeautifulSoup(response.content)
            text = soup.find('div', attrs={'class': 'propertydescriptionfull'}).text.lower()
            text += soup.find('div', attrs={'class': 'propertyfeature'}).text.lower()
            if not all([reqd_string.lower() in text
                        for reqd_string in required_description_strings]):
                continue
        print FULL_COTTAGE_URL.format(cottage_url), price


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Find cottages to stay in'
                                                 ' using cottages4you.co.uk.')
    parser.add_argument('--start-date', metavar='DD-MM-YYYY', required=True)
    parser.add_argument('--nights', type=int, default=7,
                        help="The number of nights the cottage should be"
                             " available for (defaults to 7).")
    parser.add_argument('--price-point', metavar='GBP', type=int,
                        help="The maximum you want the cottage to cost for"
                             " the week.")
    parser.add_argument('--description-contains', metavar='TEXT',
                        action='append',
                        help="A string you want the description of the"
                             " cottage to include. Can be specified multiple"
                             " times, all specified strings must be present"
                             " for a cottage to be output.")
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG,
                            format="%(asctime)s %(levelname)s %(message)s")
    if not re.match('([0-9]{2}-){2}[0-9]{4}', args.start_date):
        parser.error('Start date not in format DD-MM-YYYY')
    filter_cottages(args.start_date, args.nights, args.price_point,
                    args.description_contains)
