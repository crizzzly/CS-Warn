import json
import os
from datetime import datetime
from pprint import pprint
from weather_data import WeatherData


weather = WeatherData()
weather.update_weather_data()
weather.plot_data()
weather.check_for_changes()

cs_warnings_hourly = [1]
if weather.should_alert:
	pass
	# bot.send_image('figures/df_hourly.png')
	# bot.send_msg(cs_warnings_hourly)
	# bot.send_msg(cs_warnings_daily)
