import json
import requests


def get_category_id(category_name):
    categories_end_point = 'http://localhost:8080/api/categories'
    response = requests.get(categories_end_point)
    categories = response.json()
    category_id = [c.get('id') for c in categories if c.get('name') == category_name][0]
    return category_id


def get_existing_titles_in_data_base(category_filter):
    # use the search by category endpoint to get activities specific to a category
    search_by_categories_end_point = 'http://localhost:8080/api/activities/search-by-categories'
    headers = {'accept': 'application/json', 'content-Type': 'application/json'}
    payload = json.dumps({'categories': [category_filter]})
    response = requests.post(search_by_categories_end_point, headers=headers, data=payload)
    activities = response.json()
    database_titles = [a.get('title') for a in activities]
    return database_titles


def inject(data):
    activity_injection_end_point = 'http://localhost:8080/api/activities/add-new'
    headers = {'accept': 'application/json', 'content-Type': 'application/json'}
    payload = json.dumps(data)
    requests.post(activity_injection_end_point, headers=headers, data=payload)




