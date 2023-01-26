import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pandas import DateOffset
import api_talk

FROM_FILE = True
TIME_ZONE = 'Europe/Berlin'
LABEL_FONTSIZE = 10
TICKLABEL_SIZE_Y = 'medium'
TICKLABEL_SIZE_X = 'xx-small'

col_probability = 'mediumvioletred'
col_wind = 'deepskyblue'
col_highlight = 'silver'
col_humidity = 'mediumblue'
col_temp = 'mediumspringgreen'
col_dew_point = 'aquamarine'


class WeatherData:
	def __init__(self, t='one_call'):
		self.type = t
		self.df = None
		self.sunsets = []
		self.sunrises = []
		self.ids = []
		self.moon = []

		if t == '5d_forecast': # !! Only in 3h-Steps available
			self.process_5d_forecast()
		elif t == 'one_call':
			self.process_onecall()

	def plot_data(self):
		plt.close()
		plt.style.use('dark_background')

		fig, axs = plt.subplots(
			2, 1,
			constrained_layout=True,
			sharex='col',
		)

		# Axis Limits
		ax1 = axs[0]
		ax1.set_xlim(self.df.dt.min(), self.df.dt.max())
		ax1.set_ylim(0, 199)

		#
		# ------------------ 1st Plot ------------------ #
		#
		# ---------- Left Axis: Probability ---------- #
		# ----- Styling ----- #
		ax1.tick_params(
			axis='y',
			labelcolor=col_probability,
			labelsize=TICKLABEL_SIZE_Y,
		)
		ax1.set_title(
			f'CS Probability within the next hours'
		)
		ax1.set_ylabel(
			'Probability in %',
			color=col_probability,
			fontsize=LABEL_FONTSIZE,
		)

		# ----- Plot ----- #

		# CS Area ---------- #
		ax1.fill_between(
			self.df.dt,
			100,
			where=self.df.probability >= 40,
			facecolor=col_highlight,
			alpha=0.5
		)

		# Probability ---------- #
		ax1.plot(
			self.df.dt,
			self.df.probability,
			color=col_probability
		)

		# ---------- Right Axis: Wind & Gust Speed ---------- #

		# ----- Styling ----- #
		ax2 = axs[0].twinx()
		ax2.tick_params(
			axis='y',
			labelcolor=col_wind,
			labelsize='medium'
		)
		ax2.set_ylabel(
			'Wind Speed and Gust in km/h',
			color=col_wind
		)

		# ----- Plot ----- #

		# Wind Speed ---------- #
		ax2.plot(
			self.df.dt,
			self.df.wind_speed,
			color=col_wind,
			linewidth=1
		)

		# Gust Speed ---------- #
		ax2.plot(
			self.df.dt,
			self.df.wind_gust,
			color=col_wind,
			linestyle='dashed',
			linewidth=1
		)

		# ------------------ 2nd Plot ------------------ #
		ax_bar = axs[1]
		ax_bar.set_title(
			'Temperature DewPoint and Humidity',
			color='white'
		)

		# ---------- Left Axis: Humidity ---------- #

		# ----- Styling ----- #
		ax_bar.tick_params(
			axis='y',
			labelsize='medium',
			color='mediumblue',
		)
		ax_bar.set_ylabel(
			'Humidity in %',
			color='mediumblue',
			fontsize=10
		)

		# ----- Plot ----- #

		# Humidity Bar ---------- #
		ax_bar.bar(
			self.df.dt,
			self.df.humidity,
			color=col_humidity,
			label='date',
			alpha=0.5,
			align='center',
			width=50,
		)

		# CS Area ---------- #
		ax_bar.fill_between(
			self.df.dt,
			100,
			where=self.df.probability >= 40,
			facecolor=col_highlight,
			alpha=0.5
		)

		# ---------- Right Axis: Temperature, Dew Point ---------- #
		ax_temp = axs[1].twinx()

		# ----- Styling ----- #
		ax_temp.tick_params(
			axis='y',
			labelcolor='aqua'
		)
		ax_temp.set_ylabel(
			'Temperature and DewPoint in °C',
			color='aqua',
			fontsize=10
		)

		# ----- Plot ----- #

		# Temperature ---------- #
		ax_temp.plot(
			self.df.dt,
			self.df.temp,
			color=col_temp,
			linewidth=1
		)

		# Dew Point ---------- #
		ax_temp.plot(
			self.df.dt,
			self.df.dew_point,
			color=col_dew_point,
			linewidth=1,
			linestyle='dashed'
		)

		# ---------- X-Axis Labels ---------- #
		minor_labels = [pd.Timestamp(self.df.sunset[0], unit='s').hour, pd.Timestamp(self.df.sunrise[0], unit='s').hour]
		minor_labels.sort()

		for ax in axs:
			ax.grid(True)
			ax.xaxis.set_major_locator(mdates.DayLocator())
			ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=minor_labels))
			ax.xaxis.set_major_formatter(mdates.DateFormatter('%A'))
			ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))

			for label in ax.get_xticklabels(minor=False):
				label.set_horizontalalignment('center')

			ax.tick_params(
				axis='x',
				which='major',
				labelsize='small',
				pad=8,
				labelbottom=True,
				direction='out'
			)
			ax.tick_params(
				axis='x',
				which='minor',
				labelsize='xx-small',
				color='silver',
				grid_color='white',
				grid_alpha=0.5,
				labelbottom=True,
				pad=2,
			)

		plt.savefig(f'figures/df_hourly.png')

	def process_onecall(self):
		if FROM_FILE:
			with open('files/weather_data_onecall.json') as file:
				data = json.load(file)
		else:
			data = api_talk.get_onecall_forecast()
			with open('files/weather_data_onecall.json', 'w') as file:
				file.write(json.dumps(data))

		self.df = pd.DataFrame(data['hourly'])
		self.df['probability'] = 100 - self.df.clouds

		self.df.dt = pd.to_datetime(self.df.dt, utc=True, unit='s', origin='unix')
		self.df['date'] = self.df.dt.dt.strftime('%Y-%m-%d')
		self.df.dt.dt.tz_convert(TIME_ZONE)

		df_daily = pd.DataFrame(data['daily'])
		df_daily.dt = pd.to_datetime(df_daily.dt, utc=True, unit='s', origin='unix')
		df_daily.sunrise = pd.to_datetime(df_daily.sunrise, utc=True, unit='s', origin='unix')
		df_daily.sunset = pd.to_datetime(df_daily.sunset, utc=True, unit='s', origin='unix')
		df_daily.dt.dt.tz_convert(TIME_ZONE)
		df_daily.sunrise.dt.tz_convert(TIME_ZONE)
		df_daily.sunset.dt.tz_convert(TIME_ZONE)
		df_daily['date'] = df_daily.dt.dt.strftime('%Y-%m-%d')

		print(df_daily.dtypes)
		df_daily.set_index('dt', inplace=True)
		cl = list(self.df.weather)
		cl = [el[0] for el in cl]
		w_df = pd.DataFrame(cl).fillna(0)
		self.df.weather = w_df.all

		sunrises = df_daily[['sunrise', 'date']]
		sunsets = df_daily[['sunset', 'date']]
		print(self.df.shape)

		self.df = pd.merge(
			left=self.df,
			right=sunrises,
			on='date'
		)
		self.df = pd.merge(
			left=self.df,
			right=sunsets,
			on='date'
		)
		self.sunrises = self.df.sunrise
		self.sunsets = self.df.sunset
		print(self.df.columns)
		print(self.df.shape)

	def process_5d_forecast(self):
		if FROM_FILE:
			with open('files/weather_data_48h.json') as f:
				data = json.loads(f.read())
		else:
			data = api_talk.get_5d_forecast()
			with open('files/weather_data_48h.json', 'w') as f:
				f.write(json.dumps(data))
		sunset = pd.to_datetime(data['city']['sunset'], unit='s', origin='unix', utc=True)
		sunrise = pd.to_datetime(data['city']['sunrise'], unit='s', origin='unix', utc=True)
		sunrise = sunrise.tz_convert(TIME_ZONE)
		sunset = sunrise.tz_convert(TIME_ZONE)

		self.df = pd.DataFrame(data['list'])
		self.df.dt = pd.to_datetime(self.df.dt, unit='s', origin='unix', utc=True)
		self.df.dt.dt.tz_convert(TIME_ZONE)
		self.df.set_index('dt', inplace=True)

		# Main
		w_list = list(self.df.main)
		w_df = pd.DataFrame(w_list).fillna(0)
		self.df['temp'] = w_df.temp
		self.df['feels_like'] = w_df.feels_like
		self.df['pressure'] = w_df.grnd_level
		self.df['humidity'] = w_df.humidity
		self.df['dew_point'] = self.df.temp -((100 - self.df.humidity)/5)

		# Weather
		cl = list(self.df.weather)
		cl = [el[0] for el in cl]
		w_df = pd.DataFrame(cl).fillna(0)
		self.df.weather = w_df.all

		# Clouds
		cl = list(self.df.clouds)
		w_df = pd.DataFrame(cl).fillna(0)
		self.df['clouds'] = w_df['all']
		self.df['probability'] = 100 - self.df.clouds


		# Wind
		c = list(self.df.wind)
		w_df = pd.DataFrame(c)
		self.df['wind_speed'] = w_df.speed
		self.df['wind_deg'] = w_df.deg
		self.df['wind_gust'] = w_df.gust
		self.df.drop(['wind', 'main'], axis=1)

		for i in range(self.df.index.size):
			self.sunrises.append(sunrise + DateOffset(day=i))
			self.sunsets.append(sunset + DateOffset(day=i))
		self.df['sunrise'] = self.sunrises
		self.df['sunset'] = self.sunsets


		print(self.df.sample(5))
		print(self.df.columns)



if __name__ == '__main__':

	weather = WeatherData()
	weather.plot_data()