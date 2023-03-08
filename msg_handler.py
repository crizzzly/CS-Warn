import datetime
import os
import logging

import requests
from telegram import ReplyKeyboardRemove, Update
from geopy.geocoders import Nominatim
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

ACCESS_TOKEN = os.environ.get('CS_ALERT_TELEGR_ACCESS_TOKEN')
MAX_CHARS = 4096
channel_id = '@CS_Alert_Alb'

NAME, LOCATION, EMAIL = range(3)


weather_icons = {
    '01n': '😎',
    '01': '😎',
    '02n': '🌤',
    '02': '🌤',
    '03n': '⛅',
    '03': '⛅',
    '04n': '️🌥',
    '04': '️🌥',
}  # = 🌚🌤⛅️🌥☁️

user_data = None
db_server = "http://127.0.0.1:5000/"


# Handle '/start' and '/help'
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation and asks the user about their gender."""
    user = update.message.from_user
    text = f"Hi {user.username}, I am EchoBot. I will fetch WeatherData for your location several " \
           f"times a day and send a notification if the sky will be clear within the next hours. " \
           f"At first I need a Name for my data. " \
           f"Send '/cancel' to stop me."

    await update.message.reply_text(
        text,
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME


async def new_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the name and asks for a location."""
    global user_data
    user = update.message.from_user
    user_data = update.message.text

    logging.info(f"userdata of {user.username}: \n{user.full_name, user.id, user.is_bot, user.is_premium}")
    await update.message.reply_text(
        "Gorgeous! Now, send me your location please, or send /skip to tell me the City."
    )

    return LOCATION





async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the location and asks for city."""
    user = update.message.from_user
    logging.info("User %s did not send a location.", user.first_name)
    await update.message.reply_text(
        "No problem. Just tell me a city and I will find out the coordinates"
    )

    return LOCATION


async def find_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global users_table
    user = update.message.from_user
    geolocator = Nominatim(user_agent="MyApp")
    loc = geolocator.geocode("Hyderabad")
    url = f"{db_server}/users/create?name={user_data}&telegram_uid={update.message.chat.username}&" \
          f"lat={loc.latitude}&lon{loc.longitude}"
    # res = requests.get(url)
    # res.raise_for_status()
    # print(users_table)

    print("The latitude of the location is: ", loc.latitude)
    print("The longitude of the location is: ", loc.longitude)
    logging.info(f"Location of {user.username}: \n{loc.longitude, loc.latitude}")
    await update.message.reply_text(
        "Great. That's all!"
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logging.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main():
    application = Application.builder().token(ACCESS_TOKEN).build()
    # ---------- conversation handler (States Name, Location) ---------

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT, new_user)],
            LOCATION: [
                MessageHandler(filters.LOCATION, location),
                CommandHandler('skip', skip_location)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()


if __name__ == '__main__':
    # send_image('figures/df_hourly.png')
    main()