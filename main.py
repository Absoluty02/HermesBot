from markups import *
from functions import *


def change_localization(message, boolean):
    db.get_collection('users').update_one({
        'chat_id': message.chat.id
    }, {"$set":
        {
            'localization': message.from_user.language_code if boolean is True else False
        }})
    bot.send_message(message.chat.id, "Localizzazione aggiornata")


def change_news_for_req(message):
    if type(message.text) is str:
        try:
            number = int(message.text)
            logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
            if number < 1 or number > 20 or number == logged_user['news_for_request']:
                bot.send_message(message.chat.id, "Numero inserito non valido o uguale a quello già indicato. Riprova.")
            else:
                db.get_collection('users').update_one({
                    'chat_id': message.chat.id
                }, {"$set": {
                    'news_for_request': number
                }})
                bot.send_message(message.chat.id, "Numero di notizie per richiesta modificato con successo.")

        except ValueError:
            bot.send_message(message.chat.id, "Non hai inserito un numero. Riprova.")


def add_domain(message):
    if not check_domain(message.text):
        bot.send_message(message.chat.id, "Il dominio che hai fornito non è valido, riprova con un altro")
    else:
        if save_domain(message):
            bot.send_message(message.chat.id, "Dominio registrato. Non riceverai più notizie da questo dominio")
        else:
            bot.send_message(message.chat.id, "Sembra che avevi già escluso in precedenza questo dominio, riprova con "
                                              "un altro")


def remove_excluded_domain(message):
    logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
    if not logged_user['excluded_domains']:
        bot.send_message(message.chat.id, "Al momento non hai escluso nessun dominio dalla dominio.")
    else:
        if not check_domain(message.text):
            bot.send_message(message.chat.id, "Il dominio che hai fornito non è valido, riprova con un altro")
        else:
            if remove_domain(message):
                bot.send_message(message.chat.id, "Dominio rimosso. Potrai ricevere notizie da questo dominio")
            else:
                bot.send_message(message.chat.id, "Dominio non trovato tra gli esclusi, riprova con "
                                                  "un altro")


@bot.callback_query_handler(func=lambda call: True)
def bot_callback(call):
    split_data = call.data.split("_")
    if split_data[0] == "save":
        msg = bot.reply_to(call.message, "Perfetto, dimmi con che nome vorresti salvare questo link.")
        bot.register_next_step_handler(msg, save_third_step, split_data[1])
    else:
        if split_data[0] == "searching":
            manage_search_callback(call)
        elif split_data[0] == "continue":
            manage_continue_search_callback(call)
        elif split_data[0] == "preference":
            manage_preference_callback(call)


def manage_search_callback(call):
    search_data = call.data.split("_")
    if search_data[1] == "category":
        bot.send_message(call.message.chat.id, "Dimmi la categoria di notizie a cui sei interessato",
                         reply_markup=category_search_markup_inline())

    elif search_data[1] == "tag":
        msg = bot.send_message(call.message.chat.id, "Dimmi la parola chiave a cui sei interessato")
        bot.register_next_step_handler(msg, search_for_tag, {
            'current_page': 1,
            'tag': None
        })
    else:
        search_for_category(call.message, {
            'current_page': 1,
            'category': search_data[2]
        })


def manage_continue_search_callback(call):
    data = call.data.split("_")
    if data[2] == 'yes':
        if data[3] == 'cat':
            search_for_category(call.message, {
                'current_page': int(data[5]),
                'category': data[4]
            })
        if data[3] == 'tag':
            search_for_tag(call.message, {
                'current_page': int(data[5]),
                'tag': data[4]
            })
    if data[2] == 'no':
        bot.send_message(call.message.chat.id, "Va bene, dimmi cosa posso fare per te.")
    if data[2] == 'change':
        if data[3] == "search":
            search(call.message)
        if data[3] == "cat":
            bot.send_message(call.message.chat.id, "Dimmi la categoria di notizie a cui sei interessato",
                             reply_markup=category_search_markup_inline())
        if data[3] == "tag":
            msg = bot.send_message(call.message.chat.id, "Dimmi la parole chiave a cui sei interessato")
            bot.register_next_step_handler(msg, search_for_tag, {
                'current_page': 1,
                'tag': None
            })


def manage_preference_callback(call):
    preference_data = call.data.split("_")
    if preference_data[1] == "localization-yes":
        msg = bot.send_message(call.message.chat.id, "Manda un nuovo message cosi che possa capire dove ti trovi")
        bot.register_next_step_handler(msg, change_localization, True)
    elif preference_data[1] == "localization-no":
        change_localization(call.message, False)
    elif preference_data[1] == "news-req":
        msg = bot.send_message(call.message.chat.id, "Dimmi quante notizie vuoi che ti mando. Te ne posso mandare al "
                                                     "massimo 20")
        bot.register_next_step_handler(msg, change_news_for_req)
    elif preference_data[1] == "add-domain":
        msg = bot.send_message(call.message.chat.id, "Mandami qui di seguito il dominio che vuoi escludere dalla "
                                                     "ricerca")
        bot.register_next_step_handler(msg, add_domain)
    elif preference_data[1] == "remove-domain":
        msg = bot.send_message(call.message.chat.id, "Mandami qui di seguito il dominio che vuoi rimuovere")
        bot.register_next_step_handler(msg, remove_excluded_domain)


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
                     f"gestire le tue notizie preferite.")


@bot.message_handler(commands=['salvaNotizia'])
def save_news(message):
    start = bot.send_message(message.chat.id, "Ottimo, mandami qui di seguito l'URL del sito dove hai "
                                              "notato la notizia che ti interessa")
    bot.register_next_step_handler(start, save_second_step)


def save_second_step(message):
    if not check_url(message.text):
        bot.send_message(message.chat.id, "L'URL che hai fornito non è valido, riprova con un altro link")
    else:
        saved_news = get_single_news(message.text)
        msg = bot.reply_to(message, "Perfetto, dimmi con che nome vorresti salvare questo link.")
        bot.register_next_step_handler(msg, save_third_step, saved_news['_id'])


def save_third_step(message, news_id):
    if type(message.text) is str:
        if save_user_news(news_id, message.chat.id, message):
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
    logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
    if details['category'] is None:
        results = newsapi.get_top_headlines(
            language=None if logged_user['localization'] is False else logged_user['localization'],
            category=message.text, page=details['current_page'],
            page_size=logged_user['news_for_request'])
        current_cat = message.text
    else:
        results = newsapi.get_top_headlines(
            language=None if logged_user['localization'] is False else logged_user['localization'],
            category=details['category'], page=details['current_page'],
            page_size=logged_user['news_for_request'])
        current_cat = details['category']
    if len(results["articles"]) == 0:
        bot.send_message(message.chat.id, "Non ho trovato nessuna notizia per questa categoria, riprova con un'altra")
    else:
        bot.send_message(message.chat.id, f"Ecco le notizie di pagina {details['current_page']}")
        send_news_messages(results["articles"], message.chat.id)
        bot.send_message(message.chat.id, text="Desideri altre notizie?",
                         reply_markup=continue_category_search_markup_inline(details['current_page'] + 1,
                                                                             current_cat))


def send_news_messages(news, chat_id):
    for n in news:
        curr_msg = f"<b>Titolo</b>: {n['title']}\n"
        if n['author'] is None:
            curr_msg += "<b>Autore</b>: Non fornito\n"
        else:
            curr_msg += f"<b>Autore</b> : {n['author']}\n"
        curr_msg += f"<b>Descrizione</b>: {n['description']}\n"
        curr_msg += f"<b>Link alla notizia</b>: <a href='{n['url']}'>link personalizzato</a>"
        bot.send_message(chat_id, text=curr_msg, parse_mode="HTML", reply_markup=save_markup(n['url']))


def search_for_tag(message, details):
    logged_user = db.get_collection('users').find_one({'chat_id': message.chat.id})
    excluded_domains = logged_user['excluded_domains'][0]
    for i in range(1, len(logged_user['excluded_domains'])):
        excluded_domains += f",{logged_user['excluded_domains'][i]}"

    if details['tag'] is None:
        result = newsapi.get_everything(q=message.text, page=details['current_page'],
                                        exclude_domains=excluded_domains,
                                        language=None if logged_user['localization'] is False else logged_user[
                                            'localization'],
                                        page_size=logged_user['news_for_request'],
                                        sort_by="relevancy")
        current_tag = message.text
    else:
        result = newsapi.get_everything(q=details['tag'], page=details['current_page'],
                                        exclude_domains=excluded_domains,
                                        language=None if logged_user['localization'] is False else logged_user[
                                            'localization'],
                                        page_size=logged_user['news_for_request'],
                                        sort_by="relevancy")
        current_tag = details['tag']
    if len(result["articles"]) == 0:
        bot.send_message(message.chat.id, "Non ho trovato nessuna notizia con questa parola chiave,"
                                          " riprova con un'altra parola chiave")
    else:
        bot.send_message(message.chat.id, f"Ecco le notizie di pagina {details['current_page']}")
        send_news_messages(result["articles"], message.chat.id)
        bot.send_message(message.chat.id, text="Desideri altre notizie?",
                         reply_markup=continue_tag_search_markup_inline(details['current_page'] + 1, current_tag))


@bot.message_handler(commands=['mostraNotizie'])
def show_news(message):
    news_keyboard = get_user_saved_news(message)
    if len(news_keyboard) > 0:
        markup = InlineKeyboardMarkup(news_keyboard)
        bot.send_message(message.chat.id, "Ecco la lista delle notizie salvate:", reply_markup=markup)
    else:
        bot.send_message(message.chat.id,
                         "Al momento non hai salvato nessuna notizia, per aggiungere una notizia "
                         "utilizza il comando /salvaNotizia:")


@bot.message_handler(commands=['cancellaNotizia'])
def delete_first_step(message):
    start = bot.send_message(message.chat.id, "Bene, mandami qui di seguito il nome con cui hai salvato il link"
                                              " della notizia che vuoi rimuovere dai salvati")
    bot.register_next_step_handler(start, delete_second_step)


def delete_second_step(message):
    if type(message.text) is str:
        if delete_saved_news(message):
            bot.send_message(message.chat.id, "Notizia cancellata con successo!")
        else:
            bot.send_message(message.chat.id, "Notizia non trovata, riprova con un'altro nome")


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
        for i in range(1, len(logged_user['excluded_domains'])):
            excluded_domains += f", {logged_user['excluded_domains'][i]}"

        preferences_message += f"{excluded_domains}\n"
    bot.send_message(message.chat.id, text=preferences_message, parse_mode="HTML",
                     reply_markup=preferences_markup(logged_user))


if __name__ == '__main__':
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")

        print("Initializing Database...")
        # Define the Database using Database name
        db = client[config.get('private', 'db_name')]
        # Define collection
        print("Bot Started...")
        bot.polling()
    except Exception as error:
        print('Cause: {}'.format(error))
