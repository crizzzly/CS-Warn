import json
import os
from datetime import datetime
from pprint import pprint
import msg_handler as bot
import api_talk as weather_api
from weather_data import WeatherData
DATA_FROM_FILE = True
treshold_orange = 50
treshold_green = 80


forecast = WeatherData(t='5d')
cs_data = forecast.probability.query('probability > @treshold')

cs_warnings_hourly = [1]
if len(cs_data) > 0:
	pass
	# bot.send_image('figures/df_hourly.png')
	# bot.send_msg(cs_warnings_hourly)
	# bot.send_msg(cs_warnings_daily)
