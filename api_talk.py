import requests
import json
import os

API_KEY = os.environ.get('OPEN_WEATHER_API')
onecall_endpoint = 'https://api.openweathermap.org/data/3.0/onecall'
historical_endpoint = 'https://api.openweathermap.org/data/3.0/onecall/timemachine'
roadrisk_endpoint = 'https://api.openweathermap.org/data/2.5/roadrisk'
# https://openweathermap.org/api/road-risk
LAT = os.environ.get('MY_LAT')
LON = os.environ.get('MY_LON')

STATION_1_ID = "06262"
STATION_2_ID = "04887"
MY_OWM_API_KEY = os.environ['OWM_API_KEY']
OWM_Endpoint_current = "https://api.openweathermap.org/data/2.5/weather"
# https://openweathermap.org/current
OWM_Endpoint_forecast = "https://api.openweathermap.org/data/2.5/forecast"
# https://openweathermap.org/forecast5


historical_params = {
	'lat': LAT,
	'lon': LON,
	'dt': 1674259200,  # timestamp for 21.01.2023 01:00
	'appid': API_KEY,
	'units': 'metric',
}


def get_nowcast():
	"""
	calls owm/weather
	"""
	parameters = {
		"lat": LAT,
		"lon": LON,
		"appid": MY_OWM_API_KEY,
		"units": "metric"
	}

	res = requests.get(OWM_Endpoint_current, params=parameters)
	res.raise_for_status()
	weather_data = res.json()

	with open('files/weather_data_nowcast.json', 'w') as file:
		file.write(json.dumps(weather_data))


def get_12h_forecast():
	"""
	calls owm/forecast
	saves weather_data for next 12h in files/weather_data_12h.json
	"""
	parameters = {
		"lat": LAT,
		"lon": LON,
		"appid": MY_OWM_API_KEY,
		"units": "metric"
	}

	res = requests.get(OWM_Endpoint_forecast, params=parameters)
	res.raise_for_status()
	weather_data = res.json()

	with open('files/weather_data_12h.json', 'w') as file:
		file.write(json.dumps(weather_data))


def get_onecall_forecast():
	"""
	returns: weather_data from owm_onecall formatted as json
	"""
	parameters = {
		"lat": LAT,
		"lon": LON,
		"appid": API_KEY,
		"units": "metric"
	}

	response = requests.get(onecall_endpoint, params=parameters)
	response.raise_for_status()
	return response.json()



if __name__ == '__main__':
	get_nowcast()