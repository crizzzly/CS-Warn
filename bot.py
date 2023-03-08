import os
import logging
import pprint

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
from server import index, user_add, user_list, user_detail, user_delete

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

telegram_bot_token = os.environ.get('CS_ALERT_TELEGR_ACCESS_TOKEN')
channel_id = '@CS_Alert_Alb'
MAX_CHARS = 4096

NAME, LOCATION, CITY = range(3)
user_name = ""


########################## START CONVERSATION ######################
# set up the introductory statement for the bot when the /start command is invoked
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
    global user_name
    user = update.message.from_user
    user_name = update.message.text

    logging.info(f"userdata of {user.username}: \n{user.full_name, user.id, user.is_bot, user.is_premium}")
    await update.message.reply_text(
        "Gorgeous! Now, send me your location please, or send /skip to tell me the City."
    )

    return LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the location and says bye."""
    user = update.message.from_user
    loc = update.message.location

    user_add(name=user_name, user_id=user.id, lat=loc.latitude, lon=loc.longitude)

    logging.info(
        "Location of %s: %f / %f", user_name, loc.latitude, loc.longitude
    )

    await update.message.reply_text("Great. That's all!")
    return ConversationHandler.END


async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please enter a city/town/whatever")
    return CITY


async def find_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    geolocator = Nominatim(user_agent="MyApp")
    loc = geolocator.geocode(update.message.text)

    user_add(name=user_name, user_id=user.id, lat=loc.latitude, lon=loc.longitude)

    logging.info(
        f"Location of {user_name}: {loc.latitude, loc.longitude}",
    )
    await update.message.reply_text(
        # f"answer from server: {res.text}"\
        "Great. That's all!"
    )
    return ConversationHandler.END

################### CONVERSATION END #####################


# get all users
async def list_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = user_list()
    users = [(user.name, user.lat, user.lon) for user in users]
    await update.message.reply_text(pprint.pformat(users))


async def list_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    details = user_detail(user.id)
    print(details)
    await update.message.reply_text(f'Details:\nName: {details.name}, Lat: {details.lat}, Lon: {details.lon}')


async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    print(f'deleting user {user.id}')
    user_delete(user.id)
    await update.message.reply_text(f"deleted User {user.name}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logging.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END



app = Application.builder().token(token=telegram_bot_token).build()
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME: [MessageHandler(filters.TEXT, new_user)],
        LOCATION: [
            MessageHandler(filters.LOCATION, location),
            CommandHandler('skip', skip_location)
        ],
        CITY: [MessageHandler(filters.TEXT, find_coordinates)]
    },
    fallbacks=[CommandHandler('cancel', cancel)]
)
app.add_handler(conv_handler)
app.add_handler(CommandHandler('all', list_all_users))
app.add_handler(CommandHandler('detail', list_user_detail))
app.add_handler(CommandHandler('delete', delete_user))

app.run_polling()
