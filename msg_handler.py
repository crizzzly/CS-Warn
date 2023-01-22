import os
import telebot
from enum import Enum

ACCESS_TOKEN = os.environ.get('CS_ALERT_TELEGR_ACCESS_TOKEN')
MAX_CHARS = 4096
channel_id = '@CS_Alert_Alb'

bot = telebot.TeleBot(ACCESS_TOKEN, parse_mode=None)  # You can set parse_mode by default. HTML or MARKDOWN

weather_icons = {
	'01n': '😎',
	'01': '😎',
	'02n': '🌤',
	'02': '🌤',
	'03n': '⛅',
	'03': '⛅',
	'04n': '️🌥',
	'04': '️🌥',
} # = 🌚🌤⛅️🌥☁️

def create_msg(message):
	print(f"create_message element type: {type(message)}")
	print(message)
	msg = f'{message["date"]}\n'
	msg += f'CS Probability : {message["probability"]}%\n'
	msg += f"{weather_icons[message['icon']]}: {message['clouds']}%\n"
	msg += f"{message['description']}\n"
	msg += f"Temperature 🌡: {message['temp']}\n"
	msg += f"feels like: {message['feels_like']}\n"
	msg += f"Wind speed 🌬: {message['wind_speed']}\n"
	if message['type'] == 'hourly':
		msg += f"Visibility in km 👀: {message['visibility_km']/1000}\n"
	msg += "\n\n"


	return msg

def send_msg(msg):
	if msg[0]['type'] == 'hourly':
		text = "CS Propability within the next hours: \n\n"
		print('send msg hourly')
	else:
		text = "CS Propability within the next days: \n\n"
		print('send msg daily')
	for el in msg:
		text += create_msg(el)

	bot.send_message(channel_id, text, disable_notification=False)






# Message handlers define filters which a message must pass.
# If a message passes the filter, the decorated function is called
# and the incoming message is passed as an argument.
# @bot.message_handler(commands=['start', 'help'])
# def send_welcome(message):
# 	bot.reply_to(message, 'Howdy, how are u doing?')

# A function which is decorated by a message handler can have an arbitrary name,
# however, it must have only one parameter (the message).

# another message_handler:
# This one echoes all incoming text messages back to the sender.
# It uses a lambda function to test a message.
# If the lambda returns True, the message is handled by the decorated function.
# Since we want all messages to be handled by this function, we simply always return True.
# @bot.message_handler(func=lambda m: True)
# def echo_all(message):
# 	bot.reply_to(message, message.text)

# We now have a basic bot which replies a static message to "/start" and "/help" commands
# and which echoes the rest of the sent messages.
# To start the bot, add the following to our source file:
# bot.infinity_polling()
#
# bot.send_message()