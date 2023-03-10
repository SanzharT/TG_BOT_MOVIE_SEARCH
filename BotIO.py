import logging
import requests
import json
from typing import Dict


from telegram import Update, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    filters,
    MessageHandler,
    ApplicationBuilder, 
    ContextTypes, 
    CommandHandler, 
    InlineQueryHandler, 
    CallbackQueryHandler,
    ConversationHandler)




CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)

search_keyboard = [
        ["Movie", "Show"],
        ["Episode", "Person"],
        ["List", "Done"]
    ]

search_markup = ReplyKeyboardMarkup(search_keyboard, one_time_keyboard=True)


def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])



async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

     await update.message.reply_text(
        "Please select /trending to get trending movies now, /popular to get most popular movies in database or /recommended"
        " to get most recommended movies in certain period"
    )


async def caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_caps = ' '.join(context.args).upper()
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)


async def inline_caps(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query
    if not query:
        return
    results = []
    results.append(
        InlineQueryResultArticle(
            id = query.upper(),
            title='Caps',
            input_message_content=InputTextMessageContent(query.upper())
        )
    )
    await context.bot.answer_inline_query(update.inline_query.id, results)


def link_constructor(imdb_id:str, category=None):
    '''
    Simple link constructor
    '''
    try:
        if category:
            link = 'https://www.imdb.com/name/' + imdb_id + '/'
        else:
            link = 'https://www.imdb.com/title/' + imdb_id + '/'
    except:
        link = 'None'
    return link


async def trending_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):

    '''
    Function that returns trending 5 movies: Name, year and link to Imdb
    '''

    response = requests.get(base_url + '/movies/trending', headers = headers)

    if response.status_code != 200:
        raise Exception("Sorry, there is error while pulling data from database.")

    result_content = json.loads(response.content)[:5]
    # Final text that user will see
    output_to_return = ''

    for i in range(len(result_content)):

        link_to_imdb = link_constructor(result_content[i]['movie']['ids']['imdb'])
    
        output_to_return += f"{i + 1}. {result_content[i]['movie']['title']} ({result_content[i]['movie']['year']}) Imdb: {link_to_imdb} \n ______________________________  \n \n"

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = output_to_return
    )



async def popular_movies(update: Update, context: ContextTypes.DEFAULT_TYPE):

    '''
    Function that returns 5 most popular movies in database: Name, year, link
    '''

    response = requests.get(base_url + '/movies/popular', headers = headers)

    if response.status_code != 200:
        raise Exception("Sorry, there is error while pulling data from database.")

    result_content = json.loads(response.content)[:5]
    # Final text that user will see
    output_to_return = ''

    for i in range(len(result_content)):

        link_to_imdb = link_constructor(result_content[i]['ids']['imdb'])
    
        output_to_return += f"{i + 1}. {result_content[i]['title']} ({result_content[i]['year']}) Imdb: {link_to_imdb} \n ______________________________  \n \n"

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = output_to_return
    )


async def most_watched(update: Update, context: ContextTypes.DEFAULT_TYPE):
    '''
    Function that will return most watched movies in the specified period
    Input: period
    '''
    # Possible options for period
    keyboard = [
        [
            InlineKeyboardButton("daily", callback_data="daily")
        ],
        [
            InlineKeyboardButton("weekly", callback_data="weekly")
        ],
        [    
            InlineKeyboardButton("monthly", callback_data="monthly")
        ],
        [  
            InlineKeyboardButton("yearly", callback_data="yearly")
        ],
        [
            InlineKeyboardButton("all", callback_data="all")
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text("Please, choose a period:", reply_markup=reply_markup)


async def most_watched_button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    selected_period = query.data

    response = requests.get(base_url + f'/movies/recommended/{selected_period}', headers = headers)
    
    if response.status_code != 200:
        raise Exception("Sorry, there is error while pulling data from database.")

    result_content = json.loads(response.content)[:5]
    # Final text that user will see
    output_to_return = ''

    for i in range(len(result_content)):

        link_to_imdb = link_constructor(result_content[i]['movie']['ids']['imdb'])
    
        output_to_return += f"{i + 1}. {result_content[i]['movie']['title']} ({result_content[i]['movie']['year']}). Movie was recommended by {result_content[i]['user_count']} users. \n Imdb: {link_to_imdb} \n ______________________________  \n \n"

    await context.bot.send_message(
        chat_id = update.effective_chat.id,
        text = output_to_return
    )


CHOOSING, TYPING_REPLY, TYPING_CHOICE = range(3)



def facts_to_str(user_data: Dict[str, str]) -> str:
    """Helper function for formatting the gathered user info."""
    facts = [f"{key} - {value}" for key, value in user_data.items()]
    return "\n".join(facts).join(["\n", "\n"])


async def start_searching(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation and ask user for category to search."""
    await update.message.reply_text(
        "Pick an object to search"
        "Then, enter a query and hit Done button to search",
        reply_markup=search_markup,
    )

    return CHOOSING


async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Ask the user for info about the selected predefined choice."""
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"Great, you're looking for a {text.lower()}, please type a name of it")

    return TYPING_REPLY


async def received_information(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store info provided by user and ask for the next category."""
    user_data = context.user_data
    text = update.message.text
    category = user_data["choice"]
    user_data[category] = text
    del user_data["choice"]

    await update.message.reply_text(
        "Neat! Just so you know, this is what you already looking for:"
        f"{facts_to_str(user_data)}You can search more, or change your opinion"
        " on something.",
        reply_markup=search_markup,
    )

    return CHOOSING


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Display the gathered info and end the conversation."""
    user_data = context.user_data
    if "choice" in user_data:
        del user_data["choice"]

    data = [(k, v) for k, v in user_data.items()]

    category = data[0][0]
    query = data[0][1]

    response = requests.get(base_url + f'/search/{category}?query={query}', headers = headers)
    
    if response.status_code != 200:
        raise Exception("Sorry, there is error while pulling data from database.")

    category = category.lower()
    result_content = json.loads(response.content)[:5]
    # Final text that user will see
    output_to_return = ''
    if category in ['movie', 'show']:
        for i in range(len(result_content)):
            link_to_imdb = link_constructor(result_content[i][category]['ids']['imdb'])
            output_to_return += f"{i + 1}. {result_content[i][category]['title']} ({result_content[i][category]['year']}). \n Imdb: {link_to_imdb} \n ______________________________  \n \n"
    elif category == 'episode':
        for i in range(len(result_content)):

            link_to_imdb = link_constructor(result_content[i]['title']['ids']['imdb'])
        
            output_to_return += f"{i + 1}. {result_content[i]['episode']['title']} ({round(result_content[i]['score'], 2)}). \n Imdb: {link_to_imdb} \n ______________________________  \n \n"
    elif category == 'person':
        for i in range(len(result_content)):

            link_to_imdb = link_constructor(result_content[i]['person']['ids']['imdb'], category='Person')
        
            output_to_return += f"{i + 1}. {result_content[i]['person']['name']} ({round(result_content[i]['score'], 2)}). \n Imdb: {link_to_imdb} \n ______________________________  \n \n"

    await update.message.reply_text(
        output_to_return,
        reply_markup=ReplyKeyboardRemove(),
    )

    user_data.clear()
    return ConversationHandler.END




async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command")

if __name__ == '__main__':

    logging.basicConfig(
        format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level = logging.INFO
    )

    # Access token to TG bot
    access_token = ''
    # enter an access token of your bot

    # Access token to Trakt API
    trakt_api = ''
    # enter an api token

    base_url = 'https://api.trakt.tv'
    # Headers for requests
    headers = {
            'Content-Type': 'application/json',
            'trakt-api-version': '2',
            'trakt-api-key': trakt_api
        }


    application = ApplicationBuilder().token(access_token).build()

    start_handler = CommandHandler('start', start)

    caps_handler = CommandHandler('caps', caps)

    inline_caps_handler = InlineQueryHandler(inline_caps)

    trending_handler = CommandHandler('trending', trending_movies)

    popular_handler = CommandHandler('popular', popular_movies)

    recomend_handler = CommandHandler('recommended', most_watched)

    recomend_handler_resp = CallbackQueryHandler(most_watched_button)

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("search", start_searching)],
        states={
            CHOOSING: [
                MessageHandler(
                    filters.Regex("^(Movie|Show|Episode|Person|List)$"), regular_choice
                )
            ],
            TYPING_CHOICE: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")), regular_choice
                )
            ],
            TYPING_REPLY: [
                MessageHandler(
                    filters.TEXT & ~(filters.COMMAND | filters.Regex("^Done$")),
                    received_information,
                )
            ],
        },
        fallbacks=[MessageHandler(filters.Regex("^Done$"), done)],
    )


    application.add_handler(start_handler)
    application.add_handler(conv_handler)
    application.add_handler(caps_handler)
    application.add_handler(inline_caps_handler)
    application.add_handler(trending_handler)
    application.add_handler(popular_handler)
    application.add_handler(recomend_handler)
    application.add_handler(recomend_handler_resp)
    

    unknown_handler = MessageHandler(filters.COMMAND, unknown)
    application.add_handler(unknown_handler)

    application.run_polling()
