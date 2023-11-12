import re
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
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

uri = config.get('private', 'db_uri')
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client[config.get('private', 'db_name')]


def check_url(url):
    url_regex = "^((http|https)://)[-a-zA-Z0-9@:%._\\+~#?&//=]{2,256}\\.[a-z]{2,6}\\b([-a-zA-Z0-9@:%._\\+~#?&//=]*)$"
    r = re.compile(url_regex)

    if re.search(r, url):
        request = requests.get(url)
        if request.status_code == 200:
            return True
        else:
            return False
    else:
        return False


def check_domain(domain):
    domain_regex = "^(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\\.)+[A-Za-z]{2,6}$"
    r = re.compile(domain_regex)
    if re.match(r, domain):
        return True
    else:
        return False


def save_domain(message):
    domain = message.text
    user_chat_id = message.chat.id

    existing_user_with_domain = db.get_collection('users').find_one({
        "chat_id": user_chat_id,
        "excluded_domains": domain
    })
    if not existing_user_with_domain:
        db.get_collection('users').update_one({
            'chat_id': user_chat_id
        },
            {"$addToSet": {
                'excluded_domains': domain
            }})
        return True
    else:
        return False


def remove_domain(message):
    domain = message.text
    user_chat_id = message.chat.id
    print("ciao")
    existing_user_with_domain = db.get_collection('users').find_one({
        "chat_id": user_chat_id,
        "excluded_domains": domain
    })
    if existing_user_with_domain:
        # db.get_collection('users').update_one({
        #     'chat_id': user_chat_id
        # },
        #     {"$pull": {
        #         'excluded_domains': {
        #             '$in': [domain]
        #         }
        #     }})
        return True
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
        saved_news = db.get_collection('news').find_one({
            'url': url_site,
            'interested_users': {
                "user_chat_id": user_chat_id
            }
        })
        if not saved_news:
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


def get_user_saved_news(message):
    news = db.get_collection('news').find({
        'interested_users.user_chat_id': message.chat.id
    })
    keyboard = []

    for n in news:
        for user in n['interested_users']:
            if user['user_chat_id'] == message.chat.id:
                tempButton = InlineKeyboardButton(text=user['name'], url=n['url'])
                keyboard.append([tempButton])
        print("fatto")
    return keyboard
