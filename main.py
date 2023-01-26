import json
import os
from datetime import datetime
from pprint import pprint
import msg_handler as bot
import api_talk as weather_api
import plot_data

DATA_FROM_FILE = True
forecasts = ["hourly", "daily"]



weather_ids_hourly= plot_data.get_hourly_weather_ids()
hourly, daily = plot_data.get_hourly_weather_ids()

cs_warnings_hourly = [1]
if len(cs_warnings_hourly) > 0:
	plot_data.get_hourly_plot()
	# bot.send_image('figures/df_hourly.png')
	# bot.send_msg(cs_warnings_hourly)
	# bot.send_msg(cs_warnings_daily)
# with open('files/cs_data_daily.json', 'w') as file:
# 	file.write(json.dumps(cs_warnings_daily))
# with open('files/cs_data.json_hourly', 'w') as file:
# 	file.write(json.dumps(cs_warnings_hourly))
