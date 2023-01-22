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