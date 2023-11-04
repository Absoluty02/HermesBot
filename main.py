import re

import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
import configparser
from functions import check_url, save_news_url
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
    markup.add(
        InlineKeyboardButton("Categoria", callback_data="cat"),
        InlineKeyboardButton("Parola chiave", callback_data="tag")
    )
    return markup


def continue_category_search_markup_inline(current_page, category):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Si", callback_data="searching_yes_cat_" + category + "_"
                                                 + str(current_page)),
        InlineKeyboardButton("No", callback_data="searching_no"),
        InlineKeyboardButton("Cambia categoria", callback_data="searching_change_cat"),
        InlineKeyboardButton("Cambia ricerca", callback_data="searching_change_search")
    )
    return markup


def continue_tag_search_markup_inline(current_page, tag):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Si", callback_data="searching_yes_tag_" + tag + "_" + str(current_page)),
        InlineKeyboardButton("No", callback_data="searching_no"),
        InlineKeyboardButton("Cambia parola chiave", callback_data="searching_change_tag"),
        InlineKeyboardButton("Cambia ricerca", callback_data="searching_change_search")
    )
    return markup


def preferences_markup(user):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Cambia numero", callback_data="news_req"),
        InlineKeyboardButton("Disattiva localizzazione", callback_data="localization") if user['localization'] else
        InlineKeyboardButton("Attiva localizzazione", callback_data="localization"),
        InlineKeyboardButton("Aggiungi dominio", callback_data="add_domain"),
        InlineKeyboardButton("Rimuovi dominio", callback_data="remove_domain")
    )
    return markup


@bot.callback_query_handler(func=lambda call: True)
def bot_callback(call):
    if call.data == "cat":
        msg = bot.send_message(call.message.chat.id, "Dimmi la categoria di notizie a cui sei interessato")
        bot.register_next_step_handler(msg, search_for_category, {
            'current_page': 1,
            'category': None
        })
    elif call.data == "tag":
        msg = bot.send_message(call.message.chat.id, "Dimmi la fonte di notizie a cui sei interessato")
        bot.register_next_step_handler(msg, search_for_tag, {
            'current_page': 1,
            'tag': None
        })
    else:
        print("ciao")
        r1 = r'yes'
        r2 = r'no'
        r3 = r'change'
        if re.search(r1, call.data):
            print("ciaociao")
            data = call.data.split("_")
            if data[1] == 'cat':
                search_for_category(call.message, {
                    'current_page': int(data[4]),
                    'category': data[3]
                })
            if data[1] == 'tag':
                print("ciaociaociao")
                search_for_tag(call.message, {
                    'current_page': int(data[4]),
                    'tag': data[3]
                })
        if re.search(r2, call.data):
            pass
        if re.search(r3, call.data):
            data = call.data.split("_")
            if data[2] == "search":
                search(call.message)
            if data[2] == "cat":
                msg = bot.send_message(call.message.chat.id, "Dimmi la categoria di notizie a cui sei interessato")
                bot.register_next_step_handler(msg, search_for_category, {
                    'current_page': 1,
                    'category': None
                })
            if data[2] == "tag":
                msg = bot.send_message(call.message.chat.id, "Dimmi la fonte di notizie a cui sei interessato")
                bot.register_next_step_handler(msg, search_for_tag, {
                    'current_page': 1,
                    'tag': None
                })


@bot.message_handler(commands=['start'])
def start_conversation(message):
    existing_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
    if not existing_user:
        db.get_collection('users').insert_one({
            'chat_id': message.chat.id,
            'username': message.chat.first_name,
            'localization': False,
            'news_for_request': 5,
            'excluded_domains': [],
            'news': []})

    bot.send_message(message.chat.id,
                     f"Benvenuto {message.chat.first_name}, io sono Hermes, utilizza i comandi per poter "
                     f"gestire le tue notizie preferite: ")


@bot.message_handler(commands=['salvaNotizia'])
def save_news(message):
    start = bot.send_message(message.chat.id, "Ottimo, mandami qui di seguito l'URL del sito dove hai "
                                              "notato la notizia che ti interessa")
    bot.register_next_step_handler(start, save_second_step)


def save_second_step(message):
    if not check_url(message.text):
        bot.send_message(message.chat.id, "L'URL che hai fornito non è valido, riprova con un altro link")
    else:
        url_site = message
        msg = bot.reply_to(message, "Perfetto, dimmi con che nome vorresti salvare questo link.")
        bot.register_next_step_handler(msg, save_third_step, url_site)


def save_third_step(message, url_site):
    if type(message.text) is str:
        if save_news_url(url_site, message):
            bot.send_message(message.chat.id, "Link alla notizia aggiunto con successo!")
        else:
            bot.send_message(message.chat.id, "Sembra che avevi già salvato in precedenza questo link, riprova con un "
                                              "altro")
    else:
        bot.send_message(message.chat.id, "Nome inserito non valido, riprova")


@bot.message_handler(commands=['cercaNotizia'])
def search(message):
    bot.send_message(message.chat.id, "Bene, dimmi rispetto a cosa vuoi cercare le notizie che ti interessano",
                     reply_markup=search_markup_inline())


def search_for_category(message, details):
    bot.send_message(message.chat.id, f"Ecco le notizie di pagina {details['current_page']}")
    logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})

    if details['category'] is None:
        results = newsapi.get_top_headlines(category=message.text, page=details['current_page'],
                                            page_size=logged_user['news_for_request'])
        current_cat = message.text
    else:
        results = newsapi.get_top_headlines(category=details['category'], page=details['current_page'],
                                            page_size=logged_user['news_for_request'])
        current_cat = details['category']
    send_news_messages(results["articles"], message.chat.id)
    bot.send_message(message.chat.id, text="Desideri altre notizie?",
                     reply_markup=continue_category_search_markup_inline(details['current_page'] + 1,
                                                                         current_cat))


def send_news_messages(news, chat_id):
    for n in news:
        print(n)
        curr_msg = f"<b>Titolo</b>: {n['title']}\n"
        if n['author'] is None:
            curr_msg += "<b>Autore</b>: Non fornito\n"
        else:
            curr_msg += f"<b>Autore</b> : {n['author']}\n"
        curr_msg += f"<b>Descrizione</b>: {n['description']}\n"
        curr_msg += f"<b>Link alla notizia</b>: <a href='{n['url']}'>link personalizzato</a>"
        bot.send_message(chat_id, text=curr_msg, parse_mode="HTML")


def search_for_tag(message, details):
    bot.send_message(message.chat.id, f"Ecco le notizie di pagina {details['current_page']}")
    logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
    if details['tag'] is None:
        result = newsapi.get_everything(q=message.text, page=details['current_page'],
                                        page_size=logged_user['news_for_request'], sort_by="relevancy")
        current_tag = message.text
    else:
        result = newsapi.get_everything(q=details['tag'], page=details['current_page'],
                                        page_size=logged_user['news_for_request'], sort_by="relevancy")
        current_tag = details['tag']
    send_news_messages(result["articles"], message.chat.id)
    bot.send_message(message.chat.id, text="Desideri altre notizie?",
                     reply_markup=continue_tag_search_markup_inline(details['current_page'] + 1, current_tag))


@bot.message_handler(commands=['visualizzaNotizie'])
def show_news(message):
    logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})


@bot.message_handler(commands=['gestisciPreferenze'])
def manage_preferences(message):
    logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
    preferences_message = (f"Eccoti un riassunto delle preferenze che hai indicato al bot."
                           f" Se non ne hai indicato, ci saranno preferenze di base.\n\n")
    preferences_message += f"<b>Numero di notizie per azione</b>: {logged_user['news_for_request']}\n"
    if logged_user['localization'] is False:
        preferences_message += "<b>Notizie localizzate in base al paese</b>: ❌\n"
    else:
        preferences_message += "<b>Notizie localizzate in base al paese</b>: ✅\n"
    if len(logged_user['excluded_domains']) == 0:
        preferences_message += "<b>Domini esclusi</b>: Nessuno\n"
    else:
        excluded_domains = f"<b>Domini esclusi</b>: {logged_user['excluded_domains'][0]}"
        for d in logged_user['excluded_domains']:
            excluded_domains += f", {d}"

        preferences_message += f"{excluded_domains}\n"
    bot.send_message(message.chat.id, text=preferences_message, parse_mode="HTML",
                     reply_markup=preferences_markup(logged_user))


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
