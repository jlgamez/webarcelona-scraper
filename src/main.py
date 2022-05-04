import logging
import requests
from bs4 import BeautifulSoup
import injector_service.injector as injector
import concurrent.futures

# logging config
logging.basicConfig(format='[%(asctime)s][%(levelname)s][%(threadName)s] %(message)s', level=logging.DEBUG)
logger = logging.getLogger()

base_url = 'https://www.webarcelona.net/barcelona-events/'
web_barcelona_html = requests.get(base_url).text
soup = BeautifulSoup(web_barcelona_html, 'html.parser')


def find_link_of_category(category_name):
    category_a_tag = soup.find('a', attrs={'title': category_name})
    logger.debug('Extracting "' + category_name + '" link from ' + str(category_a_tag))
    category_link = category_a_tag.get('href')
    logger.debug(category_name + ' link is ' + str(category_link))
    return category_link


def get_events_list(category_url):
    category_page_html = requests.get(category_url).text
    category_soup = BeautifulSoup(category_page_html, 'html.parser')
    events_div_container = category_soup.select_one('div[id^="block-views-block-last-events-block-"]')
    return events_div_container.findAll('li', attrs={'class': 'col-md-6'})


def extract_event_title_and_url(event_li):
    # urls do not come complete, add the protocol and domain name before returning the url
    base_domain = 'https://www.webarcelona.net'
    event_a_tag = event_li.select_one('li.col-md-6  div.views-field-title a')
    event_title = str(event_a_tag.string)
    event_url = base_domain + event_a_tag.get('href')
    return event_title, event_url


def extract_event_description(event_li):
    event_p_tag = event_li.select_one('div.views-field-body p')
    logger.debug('Got description from ' + str(event_p_tag))
    return str(event_p_tag.getText())


def extract_event_date(event_li):
    event_time_tag = event_li.select_one('div.views-field-field-event-date time')
    date_time = str(event_time_tag.attrs.get('datetime'))
    logger.debug('Extracted "' + str(date_time) + '" from ' + str(event_time_tag))
    idx = date_time.index('T')
    event_date = date_time[0:idx]
    return event_date


def extract_event_location(event_url):
    # to extract the location open the event link and extract from there
    logger.debug('Accessing the event url to get the description')
    event_page_html = requests.get(event_url).text
    event_soup = BeautifulSoup(event_page_html, 'html.parser')
    div_address = event_soup.select_one('div.block-field-blocknodeeventfield-main-event-address div.field__item')
    # control for those cases without address
    try:
        event_address = str(div_address.string)
        logger.debug('Extracted address "' + str(event_address) + '" from ' + str(div_address))
    except AttributeError:
        event_address = 'Barcelona'
        logger.debug('Address div has no text. Setting location to ' + str(event_address))

    return event_address


def scrape_data(event, category, exclude_events):
    request_body = {}
    title, url = extract_event_title_and_url(event)
    logger.debug('Extracted title: "' + str(title) + '" and bookingLink: ' + str(url))
    # in case the title is already in the database, do not
    # proceed scraping more data
    if title in exclude_events:
        logger.debug(category + ' title already in database. Interrupting scraping. "' + title + '"')
        return None

    try:
        description = extract_event_description(event)
        date = extract_event_date(event)
        location = extract_event_location(url)
        category_id = injector.get_category_id(category)
    except Exception as e:
        logger.debug(e)

    request_body['title'] = title
    request_body['description'] = description
    request_body['date'] = date
    request_body['location'] = location
    request_body['bookingLink'] = url
    request_body['categoryId'] = category_id

    logger.debug('Generated activity payload: ' + str(request_body))
    return request_body


def add_activities_to_database(activity_category):
    # load titles that are already in the database to exclude them from the scraping session
    exclude_titles = injector.get_existing_titles_in_data_base(activity_category)
    logger.debug('Extracted "' + str(activity_category) + '" titles from database: ' + str(exclude_titles))
    # map database category to webbarcelona.net category
    if activity_category == 'music':
        web_category = 'Concerts'
    elif activity_category == 'city':
        web_category = 'Experiences'
    elif activity_category == 'culture':
        web_category = 'Exhibitions'

    # get the link to the web category
    web_category_link = find_link_of_category(web_category)

    # access the web category link and fetch all events inside
    events = get_events_list(web_category_link)
    logger.debug('Extracted events from ' + str(web_category_link) + ': ' + str(events))

    # scrape the required data from each event (if the title is already
    # in the database the returned object will be None
    logger.debug('Starting data scraping from each event')
    for e in events:
        payload = scrape_data(e, activity_category, exclude_titles)
        # inject the data when the object is not None
        if payload is not None:
            try:
                injector.inject(payload)
                logger.info('Payload successfully injected in database: ' + str(payload))
            except Exception as e:
                logger.debug(e)


# scrape and inject the data asynchronously with a ThreadPoolExecutor
categories_list = ['culture', 'music', 'city']

with concurrent.futures.ThreadPoolExecutor() as executor:
    executor.map(add_activities_to_database, categories_list)
