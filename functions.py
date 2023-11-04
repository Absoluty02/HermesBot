import re

import telebot
import configparser
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from newsapi import NewsApiClient
import requests

config = configparser.ConfigParser()
config.read('config.ini')

API_KEY = config.get('private', 'bot_token')

bot = telebot.TeleBot(API_KEY)
newsapi = NewsApiClient(api_key=config.get('private', 'newsApi_key'))

uri = "mongodb+srv://BotUser:RtMw8xAdwyFjU924@clusterbot.rjqkcg5.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client[config.get('private', 'db_name')]


def check_url(url):
    regex = "^((http|https)://)[-a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)$"
    r = re.compile(regex)

    if re.search(r, url):
        request = requests.get(url)
        if request.status_code == 200:
            return True
        else:
            return False
    else:
        return False


def save_news_url(message, custom_name_message):
    url_site = message.text
    user_chat_id = message.chat.id

    existing_news = db.get_collection('news').find_one({'url': url_site})
    if not existing_news:
        print("notizia non trovata")
        db.get_collection('news').insert_one({
            'url': url_site,
            'interested_users': [{
                "user_chat_id": user_chat_id,
                "name": custom_name_message.text}
            ]
        })
        return True
    else:
        coso = db.get_collection('news').find_one({
            'url': url_site,
            'interested_users': {
                "user_chat_id": user_chat_id
            }
        })
        if not coso:
            return False
        else:
            db.get_collection('news').update_one({
                'url': url_site},
                {"$addToSet":
                    {"interested_users":
                        {
                            "user_chat_id": user_chat_id,
                            "name": custom_name_message.text
                        }}}
            )
            return True
