import csv
import logging
import os
import datetime
import pytz
import werkzeug.exceptions

# from errorhandler_bot import error_handler, bad_command
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

from server import (
    user_add,
    user_list,
    user_detail,
    user_delete,
    city_add,
    city_list,
    city_get_name,
    city_get_coord,
    new_weather_data,
)
from weather_data import WeatherData

logging.basicConfig(
    filename='logfiles/bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

telegram_bot_token = os.environ.get('CS_ALERT_TELEGR_ACCESS_TOKEN')
channel_id = '@CS_Alert_Alb'
my_id = 5897239945
MAX_CHARS = 4096

NAME, LOCATION, CITY = range(3)
user_name = ""

# with open('instance/testusers.csv') as f:
#     user_csv = csv.DictReader(f)
#     for u.


# for cty
cities = [WeatherData(city.name, city.lat, city.lon) for city in city_list()]
for c in cities:
    c.update_weather_data()
    new_weather_data(c.df, c.city)


# run once to add to db
# for cty in cities:
#     city_add(cty.city, cty.lat, cty.lon)


async def send_all_plots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    alert = False
    for city in cities:
        if city.should_alert:
            alert = True
            try:
                await update.message.reply_photo(open(f'figures/{city.city}-{city.type}.png', 'rb'))
            except Exception as e:
                print(e)
                await update.message.reply_text(f"Error while trying to send photo:\n{e}")
    if not alert:
        await update.message.reply_text("None of our friends seems to have luck")


async def send_plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command '/my_weather'
    sends last created weather plot
    :param update:
    :param context:
    :return:
    """
    u = update.message.from_user
    try:
        user = user_detail(u.id)
        try:
            await update.message.reply_photo(f'figures/{user.city}-onecall.png')
        except Exception as e:
            logging.exception(e)
            await update.message.reply_text(f"Exception while sending plot: \n{e}")

    except werkzeug.exceptions.NotFound as e:
        msg = f"Error while trying to find user_id {u.id} in db:\n No such id\n{e}"
        logging.exception(msg)
        await update.message.reply_text(msg)


# to regularly update weather data of all saved cities
async def update_weather_data(context: ContextTypes.DEFAULT_TYPE):
    """
    Updates WeatherData via weather api. Send according data to every user if this is first run per day.
    in every other run it compares if chances have changend and only alerts if so
    If there's a medium/good chance in one city it sends the plot to user group
    :param context: application context
    :return: None
    """
    users = user_list()

    logging.info("Updating Weather Data")
    # update weather data for every city
    for city in cities:
        city.update_weather_data()
        try:
            if city.should_alert:
                await context.bot.sendPhoto(channel_id, open(f'figures/{city.city}-one_call.png', 'rb'))
            else:
                await context.bot.send_message(chat_id=channel_id, text="No good chances today")
        except RuntimeWarning as w:
            logging.warning(f"Runntime warning while trying to send photo: \n{w}")
            await context.bot.send_message("Something might have gone wrong")
    # send weather plot to users
    for user in users:
        if context.job.data:
            try:
                # await update.message.reply_photo(open(f'figures/{city.city}-{city.type}.png', 'rb'))
                await context.bot.sendPhoto(user.user_id, open(f'figures/{user.city}-one_call.png', 'rb'))
            except Exception as e:
                logging.exception(f'send_plot: \n{e}')
                print(e)
                # await update.message.reply_text(f"Error while trying to send photo:\n{e}")
        else:
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


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Stores the location and says bye."""
    user = update.message.from_user
    loc = update.message.location
    locator = Nominatim(user_agent="My_App")
    city_name = locator.reverse(f"{loc.latitude}, {loc.longitude}")
    logging.info(
        "Location of %s: %f / %f", user_name, loc.latitude, loc.longitude
    )

    # check if city is in db, if not create new entry
    try:
        if not city_get_coord(city_name):
            logging.info(f"Creating new WeatherData instance for {city_name}")
            city_add(city_name, loc.latitude, loc.longitude)
            new_data = WeatherData(city=city_name, lat=loc.latitude, lon=loc.longitude)
            new_data.update_weather_data()
            new_weather_data(new_data.df, city_name)
            # cities.append(new_data)
    except LookupError as e:
        logging.error("Something went wrong while trying to create new WeatherData")
        return None

    try:
        user_add(name=user_name, city=city_name, user_id=user.id, lat=loc.latitude, lon=loc.longitude)
    except Exception as e:
        logging.error(e)
        await update.message.reply_text(f"Error: \n{e}")
        return None
    logging.info(f"created user {user} from {city_name}")

    try:
        await update.message.reply_text("Great. That's all!")
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")
        return None
    return ConversationHandler.END


async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Please enter a city/town/whatever")
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")

    return CITY


async def find_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Finds Coordinates by Name given by user
    creates new user, city&weatherdata (if needed) in db
    """
    user = update.message.from_user
    city_name = update.message.text
    geolocator = Nominatim(user_agent="MyApp")
    loc = geolocator.geocode(update.message.text)


    if loc is None:
        await update.message.reply_text(f"Can't find name {city_name}\nPlease try again")
        return None

    logging.info(
        f"Location of {user_name}: {loc.latitude, loc.longitude}",
    )

    # convert string to camelcase
    city_name = city_name[0].upper() + city_name[1:].lower()

    # check if city is in db, if not create new entry
    try:
        logging.info(f"Creating new WeatherData instance for {city_name}")
        city_add(city_name, loc.latitude, loc.longitude)
    except (Exception, TypeError) as e:
        logging.warning(e)
        logging.info("passing")
    else:
        new_data = WeatherData(city=city_name, lat=loc.latitude, lon=loc.longitude)
        await new_data.update_weather_data()
        try:
            new_weather_data(new_data.df, city_name)
            # cities.append(new_data)
        except LookupError as e:
            logging.error("Something went wrong while trying to create new WeatherData")
            return None
    finally:
        try:
            user_add(name=user_name, city=city_name, user_id=user.id)
        except Exception as e:
            await update.message.reply_text(f"Error while saving userdata: \n{e}")
            return None
        try:
            await update.message.reply_text("Great. That's all!")
        except Exception as e:
            await update.message.reply_text(f"Error: \n{e}")
        return ConversationHandler.END


################### CONVERSATION END #####################


# get all users
async def list_all_cities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends all cities stored in db"""
    try:
        users = user_list()
        msg = "Cities: \n"
        for user in users:
            msg += f"{user.city}\n"
        try:
            await update.message.reply_text(msg)
        except Exception as e:
            await update.message.reply_text(f"Error: \n{e}")
    except Exception as e:
        await update.message.reply_text(f"Error while trying to fetch users: \n{e}")


async def list_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List user detail"""
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
    """Deletes user by user_id"""
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
        # if h < 0:
        #     await update.effective_message.reply_text("Sorry we can not go back to future!")
        #     return
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(update_weather_data, due, chat_id=chat_id, name=str(chat_id), data=due)

        logging.info(f"Timer set to {due} sec")
        text = f"Timer successfully set to {due} sec!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds>")


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user has changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)


##################### Timer End ##############################


async def available_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    '/help' command shows every for user available command
    :param update:
    :param context:
    :return:
    """
    msg = "Available commands: \n " \
          "/all - lists all current saved cities \n" \
          "/start - conversation to add yourself as new user \n" \
          "/detail - show saved details \n" \
          "/delete - delete yourself from user list\n" \
          "/weather - show your latest weather data\n" \
          "/weather_all - show plots of all saved cities if there's a minimal chance"
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
    fallbacks=[CommandHandler('cancel', cancel)],
    name="new_user_conv",
    # block=True
)

app.add_handler(conv_handler)
app.add_handler(CommandHandler('all', list_all_cities))
app.add_handler(CommandHandler('detail', list_user_detail))
app.add_handler(CommandHandler('delete', delete_user))
app.add_handler(CommandHandler('weather_all', send_all_plots))
app.add_handler(CommandHandler('weather', send_plot))
app.add_handler(CommandHandler('set', set_timer))
app.add_handler(CommandHandler('unset', unset))
app.add_handler(CommandHandler('help', available_commands))
# app.add_handler(CommandHandler('bad_command', bad_command))
# app.add_error_handler(error_handler)

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
    data=True,
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
    data=False
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
    data=False
)
app.run_polling()
