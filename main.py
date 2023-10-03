import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
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
client = MongoClient(uri, server_api=ServerApi('1'))


def search_markup_inline():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(InlineKeyboardButton("Categoria", callback_data="cat", ),
               InlineKeyboardButton("Parola chiave", callback_data="tag")
               )
    return markup


@bot.message_handler(commands=["Ciao"])
def greet(message):
    print(message.chat.first_name)
    bot.reply_to(message, "Ciao a te! Bentornato su Telegram.")


@bot.message_handler(commands=["CiaoBot"])
def greetWithoutResponse(message):
    bot.send_message(message.chat.id, "Ciao a te! Bentornato su Telegram.")


@bot.message_handler(commands=['start'])
def startConversation(message):
    existing_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
    if not existing_user:
        db.get_collection('users').insert_one({
            'chat_id': message.chat.id,
            'username': message.chat.first_name
        })
    bot.send_message(message.chat.id,
                     f"Benvenuto {message.chat.first_name}, io sono Hermes, utilizza i comandi per poter "
                     f"gestire le tue notizie preferite: ")


@bot.message_handler(commands=['salvaNotizia'])
def saveNews(message):
    start = bot.send_message(message.chat.id, "Ottimo, mandami mi qui di seguito l'URL del sito dove hai "
                                              "notato la notizia che ti interessa")
    bot.register_next_step_handler(start, saveSecondStep)


@bot.message_handler(commands=['cercaNotizia'])
def search(message):
    bot.send_message(message.chat.id, "Bene, dimmi rispetto a cosa vuoi cercare le notizie che ti interessano",
                     reply_markup=search_markup_inline())


@bot.callback_query_handler(func=lambda call: True)
def search_callback(call):
    if call.data == "cat":
        msg = bot.send_message(call.message.chat.id, "Dimmi la categoria di notizie a cui sei interessato")
        bot.register_next_step_handler(msg, searchForCategory)
    if call.data == "tag":
        msg = bot.send_message(call.message.chat.id, "Dimmi la fonte di notizie a cui sei interessato")
        bot.register_next_step_handler(msg, searchForTag)


def searchForCategory(message):
    results = newsapi.get_top_headlines(category=message.text, page=1, page_size=5)
    news = results["articles"]
    for n in news:
        source = n['source']
        print(source)
        strSource = str(source)
        print(strSource)
        currMsg = "*Titolo*: " + n['source']['name']
        bot.send_message(message.chat.id, text=currMsg, parse_mode="MarkdownV2")

def searchForTag(message):
    result = newsapi.get_top_headlines(q=message.text, page=1, page_size=5)
    news = result["articles"]
    for n in news:
        currMsg = "**Titolo**: " + n["source"]
        bot.send_message(message.chat.id, text=currMsg, parse_mode="MarkdownV2")


def saveSecondStep(message):
    bot.send_message(message.chat.id, "ciao")


if __name__ == '__main__':
    try:
        print("Initializing Database...")
        # Define the Database using Database name
        db = client[config.get('private', 'db_name')]
        # Define collection
        print("Bot Started...")
        bot.polling()
    except Exception as error:
        print('Cause: {}'.format(error))
