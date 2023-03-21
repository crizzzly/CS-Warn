#!/usr/bin/env python3.11
import atexit
import datetime
import logging
import os

import pytz
import werkzeug.exceptions
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

from errorhandler_bot import error_handler
from server import (
    user_add,
    user_list,
    user_detail,
    user_delete,
    city_add,
    city_list,
    city_get_coord,
    new_weather_data,
    get_weather_data,
)
from weather_data import WeatherData


logging.basicConfig(
    filename='logfiles/bot.log',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

telegram_bot_token = os.environ.get('CS_ALERT_TELEGR_ACCESS_TOKEN')

channel_id = '@CS_Alert_Alb'
MY_ID = os.environ.get('CS_ALERT_TELEGR_ID')

MAX_CHARS = 4096

NAME, LOCATION, CITY = range(3)

# time to run code automatically [h, m]
run_times = [
    {'h': 1, 'm': 24},  # 0
    {'h': 1, 'm': 26},  # 1
    {'h': 18, 'm': 0},  # 2
    {'h': 20, 'm': 0},  # 3
]

# TODO: Exception handling is too complicated


def check_time():
    time_now = datetime.datetime.now(tz=pytz.timezone('Europe/Berlin'))

    if time_now.hour >= run_times[3]['h'] and time_now.minute >= run_times[3]['m']:
        return 3
    elif time_now.hour >= run_times[2]['h'] and time_now.minute >= run_times[2]['m']:
        return 2
    elif time_now.hour >= run_times[1]['h'] and time_now.minute >= run_times[1]['m']:
        return 1
    else:
        return 0


weather_per_city = []
# city.update_weather_data() for city in weather_per_city
for city in city_list():
    c = WeatherData(city.name, city.lat, city.lon)
    c.update_weather_data(run=check_time())
    weather_per_city.append(c)


async def send_all_plots(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for cty in weather_per_city:
        alert = True
        try:
            await update.message.reply_photo(open(f'figures/{cty.city_name}-{cty.run}.png', 'rb'))
        except (Exception, FileNotFoundError) as e:
            txt = f"bot.py: Error while trying to send photo in 'bot.py send_all_plots':"
            logging.exception(txt, e)
            await update.message.reply_text(f"{txt}:\n, {e}")
    # if not alert:
    #     await update.message.reply_text("None of our friends seems to have luck")


async def send_plot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command '/weather'
    sends last created weather plot
    :param update:
    :param context:
    :return:
    """
    u = update.message.from_user

    run = None
    for i in range(len(run_times)):
        pos = len(run_times) - i
    run = check_time()

    logging.warning(f"bot.py: Sending plot to {u.username}, id: {u.id}, chat_id{update.message.chat_id}. Number of last run: {run}")

    try:
        user = user_detail(u.id)
    except werkzeug.exceptions.NotFound as e:
        msg = f"bot.py: Error in 'bot.py send_plot':\n Error while trying to find user_id {u.id} in db:\n No such id\n{e}"
        logging.exception(msg, e)
        await update.message.reply_text(msg)
    else:
        for usr in user:
            try:
                await update.message.reply_photo(f'figures/{usr.city}-{run}.png')
            except Exception as e:
                txt = f"bot.py: Exception in 'bot.py send_plot' while sending plot:"
                logging.exception(txt, e)
                await update.message.reply_text(f"{txt}\n{e}")
            except ConnectionResetError as e:
                txt = "bot.py: ConnectionResetError in send_plot"
                logging.exception(txt, e)
                await update.message.reply_text(f"{txt}\n{e}")


# to regularly update weather data of all saved weather_per_city
async def update_weather_data(context: ContextTypes.DEFAULT_TYPE):
    """
    Updates WeatherData via weather api. Send according data to every user if this is first run per day.
    in every other run it compares if chances have changend and only alerts if so
    If there's a medium/good chance in one city_name it sends the plot to user group
    :param context: application context
    :return: None
    """
    users = user_list()
    run = context.job.data
    # TODO: Check changes func in weather_data - > simplest way? compared data?? used dataframe options accordingly?
    #  CS Marker in plotting - does it set the marker on the right position?

    logging.warning("bot.py: Updating Weather Data")
    # update weather data for every city_name and send to group if anyone has good chances
    for cty in weather_per_city:
        logging.info(f"bot.py: Updating weather data for {cty.city_name}\nRun: {run}")
        cty.update_weather_data(run=run)
        new_weather_data(cty.df, cty.city_name, run=run)
        if run == 0:
            pass
        if run > 0:
            last_weather = get_weather_data(cty.city_name, run=(run-1))
            cty.check_for_changes(last_weather)
            logging.info(f"bot.py: Should alert is set to: {cty.should_alert}\n"
                         f"sending plot for {cty.city_name} to {channel_id}\nRun: {run}")
            # logging.info(f"bot.py: sending plot for {cty.city_name} to {channel_id}\nRun: {run}")
            await context.bot.sendPhoto(channel_id, open(f'figures/{cty.city_name}-{run}', 'rb'))

        if cty.should_alert or run == 0:
            try:
                # await context.bot.send_message(channel_id, f"run: {run}, cty: {cty.city_name}")
                # await context.bot.sendPhoto(channel_id, open(f'figures/{cty.city_name}-{run}.png', 'rb'))
                for user in users:
                    if cty.city_name == user.city:
                        logging.info(f"bot.py: sending plot for {cty.city_name} to {user.name}")
                        try:
                            await context.bot.sendPhoto(user.user_id, open(f'figures/{user.city}-{run}.png', 'rb'))
                        except (Exception, FileNotFoundError) as e:
                            logging.exception(f'bot.py: send_plot  in "update_weather_data": \n{e}')
                            print(e)
            except RuntimeWarning as w:
                logging.warning(
                    f"bot.py: Runtime warning while trying to send photo in 'bot.py update_weather_data': \n{w}")
                await context.bot.send_message("Something might have gone wrong")

        elif run == 0 and not cty.should_alert:
            logging.info(f"Bot.py: No good chances for {cty.city_name}")
            # await context.bot.send_message(chat_id=channel_id, text=f"No good chances in {cty.city_name}.")
        else:
            logging.info(f"bot.py: Run number {run}. Skipping user message")


async def list_user_detail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List user detail"""
    user = update.message.from_user
    try:
        details = user_detail(user.id)
        print(details)
    except Exception as e:
        await update.message.reply_text(f"Error while fetching user data from {user.name}, id:{user.id} in 'bot.py - list_user_detail': \n{e}")
        return None
    else:
        txt = "Details:\n"
        for det in details:
            txt += f"Name: \t{det.name},\nid: \t{det.user_id},\ncity: \t{det.city}\n\n"
        try:
            await update.message.reply_text(txt)
        except Exception as e:
            await update.message.reply_text(f"Error in bot.py - list_user_detail while trying to send message: \n{e}")
            return None


async def delete_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Deletes user by user_id"""
    user = update.message.from_user
    logging.info(f'bot.py: deleting user {user.id}')
    try:
        user_delete(user.id)
        try:
            await update.message.reply_text(f"deleted User {user.name}")
        except Exception as e:
            await update.message.reply_text(f"Error: \n{e}")
    except Exception as e:
        await update.message.reply_text(f"Error while accessing user data: \n{e}")


########################## START CONVERSATION ######################
# set up the introductory statement for the bot when the /start command is invoked
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts the conversation and asks the user about their gender."""
    user = update.message.from_user
    text = f"Hi {user.username}, I am ClearSky Bot. \nI will fetch WeatherData for your location several " \
           f"times a day and send a notification if there is any CS-probability within the next 48 hours. \n" \
           f"At first I need a Name for my data. \n" \
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
    text = update.message.text
    user_name = text[0].upper() + text[1:].lower()
    context.user_data['set_name'] = user_name

    logging.info(f"bot.py: New user? {user.username}: \n{user.full_name, user.id, user.is_bot, user.is_premium}")
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
    u_name = context.user_data['set_name']
    logging.info(
        f"bot.py: Location of %s: %f / %f\n type: {type(loc.latitude)}", u_name, loc.latitude, loc.longitude
    )
    print(type(city_name))
    city_name = city_name.address.split(', ')[2]
    print(city_name)

    # check if city_name is in db, if not create new entry
    try:
        if not city_get_coord(city_name):
            logging.info(f"bot.py: Creating new WeatherData instance for {city_name}")
            city_add(city_name, loc.latitude, loc.longitude)
            new_data = WeatherData(city=city_name, lat=loc.latitude, lon=loc.longitude)
            new_data.update_weather_data()
            weather_per_city.append(new_data)
            try:
                new_weather_data(new_data.df, city_name)
            except ValueError as e:
                logging.exception("bot.py: Value error server.py new_weather_data", e)
                return None
    except LookupError as e:
        logging.error("bot.py: Something went wrong while trying to create new WeatherData", e)
        return None

    try:
        user_add(name=u_name, city=city_name, user_id=user.id)
    except Exception as e:
        logging.exception(e)
        await update.message.reply_text(f"Error: \n{e}")
        return None
    else:
        logging.info(f"bot.py: Added new user: {u_name} from {city_name}")


    try:
        await update.message.reply_text("Great. That's all!\n"
                                        "You can see the latest created weatherdata by typing '/weather'\n"
                                        "List all created plots that have CS-probability with '/weather_all'\n"
                                        f"Update times are: {run_times[0]['h']}:{run_times[0]['m']}, "
                                        f"{run_times[1]['h']}:{run_times[1]['m']}, {run_times[2]['h']}:{run_times[2]['m']}")
    except Exception as e:
        logging.exception('Error in bot.py - location', e)
        await update.message.reply_text(f"Error: \n{e}")
        return None
    return ConversationHandler.END


async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("Please enter a city_name/town/whatever")
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")

    return CITY


async def find_coordinates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Finds Coordinates by Name given by user
    creates new user, city_name&weatherdata (if needed) in db
    """
    user = update.message.from_user
    city_name = update.message.text
    geolocator = Nominatim(user_agent="MyApp")
    loc = geolocator.geocode(update.message.text)
    u_name = context.user_data['set_name']

    if loc is None:
        await update.message.reply_text(f"Can't find name {city_name}\nPlease try again")
        return None

    logging.info(
        f"bot.py: Location of {u_name}: {loc.latitude, loc.longitude}",
    )

    # convert string to camelcase
    city_name = city_name[0].upper() + city_name[1:].lower()

    # check if city_name is in db, if not create new entry
    try:
        logging.info(f"bot.py: Creating new WeatherData instance for {city_name}")
        city_add(city_name, loc.latitude, loc.longitude)
    except (Exception, TypeError) as e:
        logging.exception("Exception in bot.py - update_weather_data while trying to add new city to db:", e)
        logging.info(f"bot.py: passing")
    else:
        new_data = WeatherData(city=city_name, lat=loc.latitude, lon=loc.longitude)
        new_data.update_weather_data()
        weather_per_city.append(new_data)
        try:
            new_weather_data(new_data.df, city_name)
            # weather_per_city.append(new_data)
        except (LookupError, ValueError) as e:
            logging.exception("bot.py: Something went wrong while trying to create new WeatherData", e)
            return None

    try:
        u_id = user.id
        user_add(name=user_name, city=city_name, user_id=u_id)
    except Exception as e:
        logging.exception("bot.py: Error while adding user to db", e)
        await update.message.reply_text(f"Error while saving userdata: \n{e}")
        return None

    try:
        await update.message.reply_text("Great. That's all!\n"
                                        "You can see the latest created weatherdata for your city by typing '/weather'\n "
                                        "List all created plots that have CS-probability with '/weather_all'\n"
                                        f"Update times are: {run_times[0]['h']}:{run_times[0]['m']}, "
                                        f"{run_times[1]['h']}:{run_times[1]['m']}, {run_times[2]['h']}:{run_times[2]['m']}")
    except Exception as e:
        logging.exception("bot.py: Error", e)
        await update.message.reply_text(f"Error: \n{e}")
    return ConversationHandler.END


################### CONVERSATION END #####################


# get all users
async def list_all_cities(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends all cities stored in db"""
    try:
        users = user_list()
    except Exception as e:
        txt = f"bot.py: Error while trying to fetch users in 'list_all_cities':"
        logging.exception(txt, e)
        await update.message.reply_text(f"{txt}\n{e}")
    else:
        msg = "Cities: \n"
        for user in users:
            msg += f"{user.city}\n"
        try:
            await update.message.reply_text(msg)
        except Exception as e:
            txt = f"bot.py: Error while creating message in 'list_all_cities': "
            logging.exception(txt, e)
            await update.message.reply_text(f"{txt}\n{e}")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logging.info(f"bot.py: User %s canceled the conversation.", user.first_name)
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
        due = (int(context.args[0]), int(context.args[1]))
        # if h < 0:
        #     await update.effective_message.reply_text("Sorry we can not go back to future!")
        #     return
        job_removed = remove_job_if_exists(str(chat_id), context)
        context.job_queue.run_once(update_weather_data, due[0], chat_id=chat_id, name=str(chat_id), data=due[1])

        logging.info(f"bot.py: Timer set to {due[0]} sec")
        text = f"Timer successfully set to {due[0]} sec!"
        if job_removed:
            text += " Old one was removed."
        await update.effective_message.reply_text(text)

    except (IndexError, ValueError):
        await update.effective_message.reply_text("Usage: /set <seconds> <run>")


async def unset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove the job if the user has changed their mind."""
    chat_id = update.message.chat_id
    job_removed = remove_job_if_exists(str(chat_id), context)
    text = "Timer successfully cancelled!" if job_removed else "You have no active timer."
    await update.message.reply_text(text)
############################## Timer End ##############################


############################ Help Commands ############################
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


async def admin_commands(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    '/admin' command shows every for user available command
    :param update:
    :param context:
    :return:
    """
    msg = "Available commands: \n " \
          "/all - lists all current saved cities \n" \
          "/set x - timer for testing update_weather_data. Starts in x seconds\n" \
          "/start - conversation to add yourself as new user \n" \
          "/detail - show saved details \n" \
          "/delete - delete yourself from user list\n" \
          "/weather - show your latest weather data\n" \
          "/weather_all - show plots of all saved cities if there's a minimal chance"
    try:
        await update.message.reply_text(msg)
    except Exception as e:
        await update.message.reply_text(f"Error: \n{e}")


########################## Create Application ##########################
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
    # persistent=True,
    # block=True
)


############################## Add handlers ##############################
app.add_handler(conv_handler)
app.add_handler(CommandHandler('all', list_all_cities))
app.add_handler(CommandHandler('detail', list_user_detail))
app.add_handler(CommandHandler('delete', delete_user))
app.add_handler(CommandHandler('weather_all', send_all_plots))
app.add_handler(CommandHandler('weather', send_plot))
app.add_handler(CommandHandler('set', set_timer))
app.add_handler(CommandHandler('unset', unset))
app.add_handler(CommandHandler('help', available_commands))
app.add_handler(CommandHandler('admin', admin_commands))
# app.add_handler(CommandHandler('bad_command', bad_command))
app.add_error_handler(error_handler)

###################### Timers To Update WeatherData ######################
app.job_queue.run_daily(  # 12.00
    update_weather_data,
    days=(0, 1, 2, 3, 4, 5, 6),
    time=datetime.time(
        hour=run_times[0]['h'],
        minute=run_times[0]['m'],
        second=00,
        tzinfo=pytz.timezone("Europe/Berlin")
    ),
    data=0,
)
app.job_queue.run_daily(  # 15.00
    update_weather_data,
    days=(0, 1, 2, 3, 4, 5, 6),
    time=datetime.time(
        hour=run_times[1]['h'],
        minute=run_times[1]['m'],
        second=00,
        tzinfo=pytz.timezone("Europe/Berlin")
    ),
    data=1
)
app.job_queue.run_daily(  # 18.00
    update_weather_data,
    days=(0, 1, 2, 3, 4, 5, 6),
    time=datetime.time(
        hour=run_times[2]['h'],
        minute=run_times[2]['m'],
        second=00,
        tzinfo=pytz.timezone("Europe/Berlin")
    ),
    data=2
)
app.job_queue.run_daily(  # 20.00
    update_weather_data,
    days=(0, 1, 2, 3, 4, 5, 6),
    time=datetime.time(
        hour=run_times[3]['h'],
        minute=run_times[3]['m'],
        second=00,
        tzinfo=pytz.timezone("Europe/Berlin")
    ),
    data=3
)

# async def at_exit_0():
#     await app.stop()
#     # await app.shutdown()


atexit.register(app.stop)
app.run_polling()

