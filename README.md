# webarcelona.net-scraper
A python scraper to bring data from www.webarcelona.net.
This Python service works together with the  [events-aggregator-api](https://github.com/jlgamez/events-aggregator-api) API.
The bot is designed to scrape data from the web and inject new activities in a SQL database by making requests to the API. 
## Prerequisites
* Have a running instance of the [events-aggregator-api](https://github.com/jlgamez/events-aggregator-api) server (The bot will try to extract and inject data in the database)
* Have installed Pipenv


## Usage
* After cloning the repository in the root folder run `pipenv install` to install dependencies
* Run `pipenv shell` to launch the virtual env
* Run the bot with `python src/main.py`
