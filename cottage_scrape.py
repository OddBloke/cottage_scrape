import pprint
import re

import requests
from BeautifulSoup import BeautifulSoup


BASE_URL = "/england?adult=2&child=0&infant=0&pets=0&partyprofile=1&nights=7&start=12-10-2013&sortorder=4&trvlperiod=1"
PRICE_POINT = 300


def _get(url):
    return requests.get('http://www.cottages4you.co.uk{}'.format(url))


def scrape_page(url):
    response = _get(url)
    soup = BeautifulSoup(response.content)

    properties = soup.findAll(attrs={'class': 'rst_propertyInfo'})
    prop_prices = {}
    for prop in properties:
        prop_name = prop.find('a')['href']
        price_span = prop.find(attrs={'class': 'rst_basePrice'})
        now_price = price_span.find(attrs={'class': 'rst_spnNowPrice'})
        price_text = ''
        if now_price:
            price_text = now_price.text
        else:
            price_text = price_span.text
        match = re.search(r'[0-9]{3}.[0-9]{2}', price_text)
        prop_prices[prop_name] = float(match.group())
    pagination = soup.findAll('a', attrs={'class': 'PaginationLink'})
    next_url = None
    for pagination_link in pagination:
        if 'next' in pagination_link.text:
            next_url = pagination_link['href']
    return prop_prices, next_url


def scrape_pages():
    prices = {}
    next_url = BASE_URL
    while next_url is not None:
        price_dict, next_url = scrape_page(next_url)
        for cottage_url, price in price_dict.items():
            if price <= PRICE_POINT:
                yield cottage_url, price


def filter():
    for cottage_url, price in scrape_pages():
        response = _get(cottage_url)
        soup = BeautifulSoup(response.content)
        if ' detached' in soup.find('div', attrs={'class': 'propertydescriptionfull'}).text.lower():
            print 'http://www.cottages4you.co.uk{}'.format(cottage_url), price
        elif ' detached' in soup.find('div', attrs={'class': 'propertyfeature'}).text.lower():
            print 'http://www.cottages4you.co.uk{}'.format(cottage_url), price


pprint.pprint(filter())