#!/usr/bin/env python3.11
import logging

import requests
import json
import os
import time
import xmltodict
import pprint

# onecall
API_KEY = os.environ.get('OPEN_WEATHER_API')
onecall_endpoint = 'https://api.openweathermap.org/data/3.0/onecall'
historical_endpoint = 'https://api.openweathermap.org/data/3.0/onecall/timemachine'
LAT = os.environ.get('MY_LAT')
LON = os.environ.get('MY_LON')

STATION_1_ID = "06262"
STATION_2_ID = "04887"

# free API
MY_OWM_API_KEY = os.environ['OWM_API_KEY_OLD']
# https://openweathermap.org/current
OWM_Endpoint_current = "https://api.openweathermap.org/data/2.5/weather"
# https://openweathermap.org/forecast
OWM_Endpoint_forecast = "https://api.openweathermap.org/data/2.5/forecast"
# https://openweathermap.org/api/road-risk
roadrisk_endpoint = 'https://api.openweathermap.org/data/2.5/roadrisk'

historical_params = {
	'lat': LAT,
	'lon': LON,
	'dt': 1674259200,  # timestamp for 21.01.2023 01:00
	'appid': API_KEY,
	'units': 'metric',
}

parameters = {
		"lat": LAT,
		"lon": LON,
		"appid": MY_OWM_API_KEY,
		"units": "metric",
		#"mode": "xml",
	}

pp = pprint.PrettyPrinter(indent=4)


def call_api(endpoint, params):
	res = requests.get(endpoint, params=params)
	res.raise_for_status()
	return res


fifteen_min = 15*60
update_times = []


def get_nowcast():
	"""
	calls owm/weather
	Update times:   16:14       -> 16:13 Uhr
					17.45       -> 16:45 Uhr
					18:01       -> 17.00 Uhr
					19:31       -> 18:31 Uhr
					19:42:30    -> 18:42:30
	"""

	text = call_api(OWM_Endpoint_current, parameters).text
	weather_data = xmltodict.parse(text)

	# with open('data/weather_data_nowcast.xml', 'r') as f:
	# 	weather_data = xmltodict.parse(f.read())
	# pprint.pprint(json.dumps(weather_data), indent=4)

	now = time.strftime('%H:%M:%S')
	updated = weather_data['current']['lastupdate'].get('@value').split('T')[1]
	update_times.append({
		'now': now,
		'update_time': updated
	})
	print(update_times[-1])

	with open('data/update_times.json', 'w') as f:
		f.write(json.dumps(update_times))


def get_5d_forecast():
	"""
	calls owm/forecast
	saves weather_data for next 5d3h in data/weather_data_5d3h.json
	"""
	print('getting 5d forecast')

	res = requests.get(OWM_Endpoint_forecast, params=parameters)
	res.raise_for_status()

	with open('data/weather_data_5d3h.json', 'w') as file:
		file.write(json.dumps(res.json()))

	return res.json()


def get_onecall_forecast(lat, lon):
	"""
	returns: weather_data from owm_onecall formatted as json
	"""
	print('getting 48h forecast (onecall)')
	parameters_onecall = {
		"lat": lat,
		"lon": lon,
		"appid": API_KEY,
		"units": "metric",
	}
	try:
		response = requests.get(onecall_endpoint, params=parameters_onecall)
		response.raise_for_status()
	except requests.exceptions.ConnectionError as e:
		txt = "api_talk.py: ConnectionError while trying to get onecall forecast"
		logging.exception(txt, e)
		logging.info("api_talk.py: Trying again ... ")
		try:
			response = requests.get(onecall_endpoint, params=parameters_onecall)
			response.raise_for_status()
		except requests.exceptions.ConnectionError as e:
			logging.exception("api_talk.py: ConnectionError once more. exiting.", e)
			exit(1)
		else:
			return response.json()

	else:
		return response.json()
#
# while True:
# 	print('updating...')
# 	get_nowcast()
# 	print('waiting ... ')
# 	time.sleep(fifteen_min)

# if __name__ == '__main__':
# 	get_nowcast()