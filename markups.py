from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup


def search_markup_inline():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Categoria", callback_data="cat"),
        InlineKeyboardButton("Parola chiave", callback_data="tag")
    )
    return markup


def category_search_markup_inline():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("Tecnologia", callback_data="searching_technology")

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
        InlineKeyboardButton("Disattiva localizzazione", callback_data="localization_no") if user['localization'] else
        InlineKeyboardButton("Attiva localizzazione", callback_data="localization_yes"),
        InlineKeyboardButton("Aggiungi dominio", callback_data="add_domain"),
        InlineKeyboardButton("Rimuovi dominio", callback_data="remove_domain")
    )
    return markup