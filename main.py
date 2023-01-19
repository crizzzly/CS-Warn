# import json
import os
from datetime import datetime
import requests
from pprint import pprint

api_key = os.environ.get('OPEN_WEATHER_API')
endpoint = 'https://api.openweathermap.org/data/3.0/onecall'
LAT = 48.788792
LON = 9.934620

parameters = {
	"lat": LAT,
	"lon": LON,
	"appid": api_key,
	"units": "metric"
}

response = requests.get(endpoint, params=parameters)
response.raise_for_status()
weather_data = response.json()

forecasts = ["hourly", "daily"]

# with open('weather_data.json', 'r') as file:
# 	weather_data = json.load(file)


daily = weather_data['daily']
hourly = weather_data['hourly']
weather_ids_hourly = [hourly[i]['weather'][0]['id'] for i in range(len(hourly))]
weather_ids_daily = [daily[i]['weather'][0]['id'] for i in range(len(daily))]

cs_hours = []
for i in range(len(weather_ids_hourly)):
	if hourly[i]['dt'] > daily[0]['sunrise'] or hourly[i]['dt'] < daily[0]['sunset']:
		pass
	date = datetime.fromtimestamp(hourly[i]['dt'])
	# if weather_ids_hourly[i] == 800 or weather_ids_hourly[i] == 801:
	if weather_ids_hourly[i] == 600:
		if date.hour > 17 or date.hour < 6:
			cs_hours.append({
				'date': date.strftime('%d.%m.%Y. %H:%M'),
				'description': hourly[i]['weather'][0]['description'],
				'wind_speed': hourly[i]['wind_speed'],
				'temp': hourly[i]['temp'],
				'clouds': hourly[i]['clouds'],
				'visibility_km': hourly[i]['visibility'],

			})
for i in range(len(weather_ids_daily)):
	if daily[i]['dt'] > daily[i]['sunrise'] or daily[i]['dt'] < daily[i]['sunset']:
		pass
	date = datetime.fromtimestamp(daily[i]['dt'])
	# if weather_ids_daily[i] == 800 or weather_ids_daily[i] == 801:
	if weather_ids_daily[i] == 804:
		cs_hours.append({
			'date': date.strftime('%d.%m.%Y. %H:%M'),
			'description': daily[i]['weather'][0]['description'],
			'wind_speed': daily[i]['wind_speed'],
			'temp': daily[i]['temp'],
			'clouds': daily[i]['clouds'],
			# 'visibility': daily[i]['visibility'],
		})

pprint(cs_hours)
