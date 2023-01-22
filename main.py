import json
import os
from datetime import datetime
import requests
from pprint import pprint
import msg_handler as bot

api_key = os.environ.get('OPEN_WEATHER_API')
endpoint = 'https://api.openweathermap.org/data/3.0/onecall'
historical_endpoint = 'https://api.openweathermap.org/data/3.0/onecall/timemachine'
LAT = os.environ.get('MY_LAT')
LON = os.environ.get('MY_LON')

parameters = {
	"lat": LAT,
	"lon": LON,
	"appid": api_key,
	"units": "metric"
}

historical_params = {
	'lat': LAT,
	'lon': LON,
	'dt': 1674259200,  # timestamp for 21.01.2023 01:00
	'appid': api_key,
	'units': 'metric',


}

forecasts = ["hourly", "daily"]
def get_probability(clouds):
	return 100-clouds

response = requests.get(endpoint, params=parameters)
response.raise_for_status()
weather_data = response.json()


with open('files/weather_data.json', 'r') as file:
	# file.write(json.dumps(weather_data))  # -> change mode to r!
	weather_data = json.load(file)


daily = weather_data['daily']
hourly = weather_data['hourly']
weather_ids_hourly = [hourly[i]['weather'][0]['id'] for i in range(len(hourly))]
weather_ids_daily = [daily[i]['weather'][0]['id'] for i in range(len(daily))]
print("Weather IDs")
print(weather_ids_daily)
print(weather_ids_hourly)

cs_warnings_hourly = []
# get hourly weather data (48h)
for i in range(len(weather_ids_hourly)):
	if hourly[i]['dt'] > daily[0]['sunrise'] or hourly[i]['dt'] < daily[0]['sunset']:
		pass
	date = datetime.fromtimestamp(hourly[i]['dt'])
	# if weather_ids_hourly[i] == 600:
	# if weather_ids_hourly[i] == 800 or weather_ids_hourly[i] == 801:
	if 800 <= weather_ids_hourly[i] <= 803:
		if date.hour > 17 or date.hour < 6:
			cs_warnings_hourly.append({
				'type': 'hourly',
				'date': date.strftime('%d.%m.%Y. %H:%M'),
				'description': hourly[i]['weather'][0]['description'],
				'icon': hourly[i]['weather'][0]['icon'],
				'id': hourly[i]['weather'][0]['id'],
				'wind_speed': hourly[i]['wind_speed'],
				'feels_like': hourly[i]['feels_like'],
				'temp': hourly[i]['temp'],
				'clouds': hourly[i]['clouds'],
				'visibility_km': hourly[i]['visibility'],
				'probability': get_probability(hourly[i]['clouds']),
			})

# get daily weather data (8 days)
cs_warnings_daily = []
for i in range(len(weather_ids_daily)):
	date = datetime.fromtimestamp(daily[i]['dt'])
	# if weather_ids_daily[i] == 804 or weather_ids_daily[i] == 803:
	# if weather_ids_daily[i] == 800 or weather_ids_daily[i] == 801:
	if 800 <= weather_ids_daily[i] <= 803:
		cs_warnings_daily.append({
			'type': 'daily',
			'date': date.strftime('%d.%m.%Y'),
			'icon': hourly[i]['weather'][0]['icon'],
			'description': daily[i]['weather'][0]['description'],
			'id': daily[i]['weather'][0]['id'],
			'wind_speed': daily[i]['wind_speed'],
			'feels_like': daily[i]['feels_like'],
			'temp': daily[i]['temp'],
			'clouds': daily[i]['clouds'],
			'probability': get_probability(daily[i]['clouds']),
		})

pprint(cs_warnings_hourly)
pprint(cs_warnings_daily)
if len(cs_warnings_hourly) > 0:
	bot.send_msg(cs_warnings_hourly)
	bot.send_msg(cs_warnings_daily)
# with open('files/cs_data_daily.json', 'w') as file:
# 	file.write(json.dumps(cs_warnings_daily))
# with open('files/cs_data.json_hourly', 'w') as file:
# 	file.write(json.dumps(cs_warnings_hourly))
