import telebot
import configparser
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from newsapi import NewsApiClient

config = configparser.ConfigParser()
config.read('config.ini')

API_KEY = config.get('private', 'bot_token')

bot = telebot.TeleBot(API_KEY)
newsapi = NewsApiClient(api_key=config.get('private', 'newsApi_key'))

uri = "mongodb+srv://BotUser:RtMw8xAdwyFjU924@clusterbot.rjqkcg5.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))



