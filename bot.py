import logging
import os
import pprint
import datetime
import pytz

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from geopy.geocoders import Nominatim
from telegram import ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from server import user_add, user_list, user_detail, user_delete, new_weather_data
from weather_data import WeatherData

logging.basicConfig(
    filename='bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


telegram_bot_token = os.environ.get('CS_ALERT_TELEGR_ACCESS_TOKEN')
channel_id = '@CS_Alert_Alb'
my_id = 5897239945
MAX_CHARS = 4096

NAME, LOCATION, CITY = range(3)
user_name = ""
users_list = []
cities = [WeatherData("Heubach", 48.7913507, 9.9363623),
          WeatherData("Stuttgart", 48.7784485, 9.1800132),
          WeatherData("Bisingen", 48.3120203, 8.9163672)]


async def send_3_plots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for city in cities:
        try:
            pass
            # city.update_weather_data()
            # try:
            #     new_weather_data(city.df.to_dict())
            # except Exception as e:
            #     print(e)
            #     await update.message.reply_text(f"Error while saving weather data:\n{e}")
        except Exception as e:
            print(e)
            await update.message.reply_text(f"Error in weather_data: \n{e}")
        try:
            await update.message.reply_photo(open(f'figures/{city.city}-{city.type}.png', 'rb'))
        except Exception as e:
            print(e)
            await update.message.reply_text(f"Error while trying to send photo:\n{e}")


async def send_all_weather_data(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    for city in cities:
        try:
            # await update.message.reply_photo(open(f'figures/{city.city}-{city.type}.png', 'rb'))
            await context.bot.sendPhoto(job.chat_id, open(f'figures/{city.city}-{city.type}.png', 'rb'))
        except Exception as e:
            logging.error(f'send_all_weather_data: \n{e}')
            print(e)
            # await update.message.reply_text(f"Error while trying to send photo:\n{e}")


# to regularly update weather data of all saved cities
async def update_weather_data(context: ContextTypes.DEFAULT_TYPE):
    users = user_list()

    logging.info("Updating Weather Data")
    for city in cities:
        city.update_weather_data()
    for user in users:
        try:
            # await update.message.reply_photo(open(f'figures/{city.city}-{city.type}.png', 'rb'))
            await context.bot.sendPhoto(user.user_id, open(f'figures/{user.city}-one_call.png', 'rb'))
        except Exception as e:
            logging.error(f'send_all_weather_data: \n{e}')
            print(e)
            # await update.message.reply_text(f"Error while trying to send photo:\n{e}")


async def update_user_list():
    pass


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
    locator = Nominatim(user_agent="My_App")
    city = locator.reverse(f"{loc.latitude}, {loc.longitude}")
    logging.info(
        "Location of %s: %f / %f", user_name, loc.latitude, loc.longitude
    )
    try:
        user_add(name=user_name, city=city, user_id=user.id, lat=loc.latitude, lon=loc.longitude)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"Error: \n{e}")
    logging.info(f"created user {user} from {city}")

    try:
        if city not in user_list():
            logging.info(f"Creating new WeatherData instance for {city}")
            new_data = WeatherData(city=city, lat=loc.latitude, lon=loc.longitude)
            new_data.update_weather_data()
            new_weather_data(new_data.df)
            cities.append(new_data)
    except LookupError as e:
        logging.error("Something went wrong while trying to create new WeatherData")

    try:
        await update.message.reply_text("Great. That's all!")
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")
    return ConversationHandler.END


async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Please enter a city/town/whatever")
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")

    return CITY


async def find_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    geolocator = Nominatim(user_agent="MyApp")
    loc = geolocator.geocode(update.message.text)
    logging.info(
        f"Location of {user_name}: {loc.latitude, loc.longitude}",
    )
    try:
        user_add(name=user_name, city=update.message.text, user_id=user.id, lat=loc.latitude, lon=loc.longitude)
    except Exception as e:
        await update.message.reply_text(f"Error while saving userdata: \n{e}")
    try:
        await update.message.reply_text("Great. That's all!")
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")
    return ConversationHandler.END

################### CONVERSATION END #####################


# get all users
async def list_all_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        users = user_list()
        users = [(user.name, user.lat, user.lon) for user in users]
        try:
            await update.message.reply_text(pprint.pformat(users))
        except Exception as e:
            await update.message.reply_text(f"Error: \n{e}")
    except Exception as e:
        await update.message.reply_text(f"Error while trying to fetch users: \n{e}")


async def list_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    try:
        details = user_detail(user.id)
        print(details)
        try:
            await update.message.reply_text(f'Details:\nName: {details.name}, Lat: {details.lat}, Lon: {details.lon}')
        except Exception as e:
            await update.message.reply_text(f"Error: \n{e}")
    except Exception as e:
        await update.message.reply_text(f"Error while fetching user data: \n{e}")


async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    logging.info(f'deleting user {user.id}')
    try:
        user_delete(user.id)
        try:
            await update.message.reply_text(f"deleted User {user.name}")
        except Exception as e:
            await update.message.reply_text(f"Error: \n{e}")
    except Exception as e:
        await update.message.reply_text(f"Error while accessing user data: \n{e}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logging.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


########################### Timer #########################

def remove_job_if_exists(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove job with given name. Returns whether job was removed."""
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def set_timer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a job to the queue."""
    chat_id = update.effective_message.chat_id
    try:
        # args[0] should contain the time for the timer in seconds
        due = int(context.args[0])
        # if due < 0:
        #     await update.effective_message.reply_text("Sorry we can not go back to future!")
        #     return

        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_daily(
            send_all_weather_data,
            days=(0, 1, 2, 3, 4, 5, 6),
            time=datetime.time(
                hour=15,
                minute=due,
                second=00,
                tzinfo=pytz.timezone("Europe/Berlin")
            ),
            user_id=chat_id,  # my_id
        )

        text = "Timer successfully set!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)

##################### Timer End ##############################


async def available_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "Available commands: \n " \
          "/all:         lists all current users \n" \
          "/start:       conversation to add yourself as new user \n" \
          "/detail:      show saved details \n" \
          "/delete:      delete yourself from user list\n" \
          "/weather:     show weather from different locations"
    try:
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")

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
app.add_handler(CommandHandler('weather', send_3_plots))
app.add_handler(CommandHandler('my_weather', send_all_weather_data))
app.add_handler(CommandHandler('set', set_timer))
app.add_handler(CommandHandler('unset', unset))
app.add_handler(CommandHandler('help', available_commands))

################# Timers Update WeatherData #############
app.job_queue.run_daily(  # 12.00
            update_weather_data,
            days=(0, 1, 2, 3, 4, 5, 6),
            time=datetime.time(
                hour=12,
                minute=00,
                second=00,
                tzinfo=pytz.timezone("Europe/Berlin")
            ),
)
app.job_queue.run_daily(  # 15.00
            update_weather_data,
            days=(0, 1, 2, 3, 4, 5, 6),
            time=datetime.time(
                hour=18,
                minute=00,
                second=00,
                tzinfo=pytz.timezone("Europe/Berlin")
            ),
)
app.job_queue.run_daily(  # 18.00
            update_weather_data,
            days=(0, 1, 2, 3, 4, 5, 6),
            time=datetime.time(
                hour=18,
                minute=00,
                second=00,
                tzinfo=pytz.timezone("Europe/Berlin")
            ),
)
app.run_polling()
