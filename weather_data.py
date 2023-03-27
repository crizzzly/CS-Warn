#!/usr/bin/env python3.11
import json
import logging
import pprint

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

import api_talk

FROM_FILE = False
TIME_ZONE = 'Europe/Berlin'
LABEL_FONTSIZE = 10
TICKLABEL_SIZE_Y = 'medium'
TICKLABEL_SIZE_X = 'xx-small'

CS_TRESHOLD_LOW = 40
CS_TRESHOLD_HIGH = 70

col_probability = 'mediumvioletred'
col_wind = 'deepskyblue'
col_highlight = 'silver'
col_med_highlight = 'gainsboro'
col_humidity = 'mediumblue'
col_humidity_text = 'royalblue'
col_temp = 'mediumspringgreen'
col_dew_point = 'aquamarine'

col_chances = ['red', 'orange', 'green']
text_chances = ['Get some sleep!', "We'll see ...", 'Seems good!']


class WeatherData:
    def __init__(self, city, lat, lon, t='one_call'):
        self.city_name = city
        self.lat = lat
        self.lon = lon
        self.time_call = None
        self.type = t
        self.df = pd.DataFrame
        self.plot_title = ''
        self.tz_offset = 0
        self.ids = []
        self.icons = []
        self.probabilities = []
        self.col_cs_chance = col_chances[0]
        self.text_cs_chance = text_chances[0]
        self.should_alert = False
        self.med_chance_comp = None
        self.good_chance_comp = None
        self.last_df = None
        self.sunset = None
        self.sunrise = None
        self.run = 0

    def update_weather_data(self, run=0):
        """
        gets OWM Weather Data via api_talk.py
        saves current weather
        processes data for analysis and plotting via pandas

        input: t = 'one_call' / '5d' for one_call(48h or 8d) or 5d (every 3h) forecast
        """
        # TODO: perhaps only use the next 12h / Time till next dawn?
        self.run = run

        logging.debug(
            f"weather_data.py: Updating Weather Data. \n{self.city_name}, Run {self.run}\nFrom File: {FROM_FILE}")
        if self.type == '5d':  # !! Only in 3h-Steps available
            json_file = 'data/weather_data_5d.json'
            call_api = api_talk.get_5d_forecast
            self.plot_title = f'CS Probability within the next {5 * 24} hours'
        # elif self.t == 'one_call':
        else:
            json_file = f'data/weather_data_{self.city_name}.json'
            call_api = api_talk.get_onecall_forecast
            self.plot_title = f'CS Probability within the next {2 * 24} hours'

        # Get WeatherData
        if FROM_FILE:
            with open(json_file) as file:
                data = json.load(file)
        else:
            with open(json_file, 'w') as file:
                data = call_api(self.lat, self.lon)
                file.write(json.dumps(data))

        # ----------- for 5d forecast: ----------- #
        if self.type == '5d':
            self.df = pd.DataFrame(data['list'])
            self.tz_offset = data['city_name']['timezone']

            # sunrise and sunset
            # Convert UTC Timestamps to pd.datetime
            sunrise = pd.to_datetime(data['city_name']['sunrise'], unit='s', origin='unix', utc=True)
            sunset = pd.to_datetime(data['city_name']['sunset'], unit='s', origin='unix', utc=True)

            # Convert to local timezone
            self.df.sunrise[0] = sunrise.tz_convert(TIME_ZONE)
            self.df.sunset[0] = sunset.tz_convert(TIME_ZONE)

            # Make Dictionaries in Cells better accessable
            # Main
            w_list = list(self.df.main)
            w_df = pd.DataFrame(w_list).fillna(0)
            self.df['temp'] = w_df.temp
            self.df['feels_like'] = w_df.feels_like
            self.df['pressure'] = w_df.grnd_level
            self.df['humidity'] = w_df.humidity
            self.df['dew_point'] = self.df.temp - ((100 - self.df.humidity) / 5)

            # Clouds
            cl = list(self.df.clouds)
            w_df = pd.DataFrame(cl).fillna(0)
            self.df['clouds'] = w_df['all']

            # Wind
            c = list(self.df.wind)
            w_df = pd.DataFrame(c)
            self.df['wind_speed'] = w_df.speed
            self.df['wind_deg'] = w_df.deg
            self.df['wind_gust'] = w_df.gust
            self.df.drop(['wind', 'main'], axis=1, inplace=True)
            # print(f'wind_speed: {self.df.wind_speed}')

        else:  # onecall_api
            self.df = pd.DataFrame(data['hourly'])
            df_daily = pd.DataFrame(data['daily'])
            self.tz_offset = data['timezone_offset']
            self.time_call = data['current']['dt']
            self.time_call = pd.to_datetime(self.time_call, unit='s', origin='unix', utc=True)
            self.time_call = self.time_call.tz_convert(TIME_ZONE)

            # Sunrise and set
            # Convert UTC Timestamps to pd.datetime
            df_daily.dt = pd.to_datetime(df_daily.dt, utc=True, unit='s', origin='unix')
            df_daily.sunrise = pd.to_datetime(df_daily.sunrise, utc=True, unit='s', origin='unix')
            df_daily.sunset = pd.to_datetime(df_daily.sunset, utc=True, unit='s', origin='unix')

            # Convert to local timezone
            df_daily.dt = df_daily.dt.dt.tz_convert(TIME_ZONE)
            self.sunrise = df_daily.sunrise.dt.tz_convert(TIME_ZONE)
            self.sunset = df_daily.sunset.dt.tz_convert(TIME_ZONE)
            self.df['sunrise'] = df_daily.sunrise
            self.df['sunset'] = df_daily.sunset

        # ----------- for 5d & onecall: ----------- #
        # convert dt from int to timeseries/timestamps
        self.df.dt = pd.to_datetime(self.df.dt, unit='s', origin='unix', utc=True)
        self.df.dt = self.df.dt.dt.tz_convert(TIME_ZONE)

        # to easily check if time is at night
        self.df['is_night'] = [
            True if self.df.dt[i].time() < self.df.sunrise[0].time() or self.df.sunset[0].time() < self.df.dt[
                i].time() else False
            for i in self.df.index
        ]

        # one column for CS Probability per timestamp
        self.df['probability'] = 100 - self.df.clouds

        self.df['is_cs'] = [
            True if self.df.probability[i] > CS_TRESHOLD_LOW and self.df.is_night[i] == True else False
            for i in self.df.index
        ]

        # make weather id and icon easily accessible
        w = list(self.df.weather)
        w = [el[0] for el in w]
        w_df = pd.DataFrame(w).fillna(0)  # create a new dataframe
        self.df['weather_id'] = w_df.id
        self.df['weather_main'] = w_df.main
        self.df['weather_description'] = w_df.description
        self.df['weather_icon'] = w_df.icon
        self.df.drop('weather', axis=1, inplace=True)
        self.ids = self.df.weather_id
        self.probabilities = self.df['probability']

        # Kick unused Columns
        self.df = self.df[[
            'dt', 'temp', 'humidity', 'clouds', 'dew_point', 'wind_speed',
            'wind_deg', 'wind_gust', 'is_night', 'probability', 'is_cs'
        ]]

        logging.info(f'weather_data.py: DataFrame for {self.city_name} created. Data from {self.time_call}')
        print(f"{self.city_name}-{self.run}: NEW DATA ---- NEW DATA ---- NEW DATA ")
        # pprint.pprint(self.df[["dt", "probability", "is_night"]])

        probs = self.df.query("is_night == True")
        good_chance = probs.query("probability >= @CS_TRESHOLD_HIGH")
        logging.info("THIS SHOULD ONLY CONTAIN ROWS AT NIGHT WITH GOOD CHANCES")
        # logging.info(f'weather_data.py: {good_chance.shape[0]} hours with good chances.')
        med_chance = probs.query("probability >= @CS_TRESHOLD_LOW")
        # logging.info(f'weather_data.py: {med_chance.shape[0]} hours with medium chances')

        # TODO: needs a checkup
        if good_chance.shape[0] > 2:
            logging.info(f"weather_data.py: CS Probability over {CS_TRESHOLD_HIGH}% on {good_chance.shape[0]} hours")
            self.text_cs_chance = text_chances[2]
            self.col_cs_chance = col_chances[2]
            self.should_alert = True
            logging.info(f'weather_data.py: good times should be {good_chance.dt}')
            logging.info("Should Warn was set to True")
        elif med_chance.shape[0] > 0:
            logging.info(f"weather_data.py: CS Probability over {CS_TRESHOLD_LOW}% on {med_chance.shape[0]} hours")
            logging.info(f'weather_data.py: medium times should be {med_chance.dt}')
            self.text_cs_chance = text_chances[1]
            self.col_cs_chance = col_chances[1]
            self.should_alert = True
            logging.info("Should Warn was set to True")
        else:
            logging.info('No good chances within the next hours')
            self.text_cs_chance = text_chances[0]
            self.col_cs_chance = col_chances[0]
            self.should_alert = False

        self.plot_data()

        # only alert if anything has chanced
        if self.run > 0:
            # compare old an new dataframes
            self.check_for_changes()

        self.med_chance_comp = med_chance
        self.good_chance_comp = good_chance

    def plot_data(self):
        """
        Plots the most important values (probability, temp, humidity, wind) via matplotlib
        """
        plt.close()
        plt.style.use('dark_background')
        logging.info("Creating Plot")

        fig, axs = plt.subplots(
            2, 1,
            constrained_layout=True,
            sharex='col',
        )

        fig.suptitle(
            f"{self.df.dt[0].strftime('%d.%m.%Y - %H:%M')}\n{self.city_name}-{self.run}: {self.text_cs_chance}",
            fontsize='xx-large',
            color=self.col_cs_chance
        )

        # Axis Limits
        ax1 = axs[0]
        ax1.set_xlim(self.df.dt.min(), self.df.dt.max())
        ax1.set_ylim(0, 100)

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
            "\n" + self.plot_title
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
            where=(self.df.probability >= CS_TRESHOLD_LOW) & (self.df.is_night == True),
            facecolor=col_highlight,
            alpha=0.5
        )
        ax1.fill_between(
            self.df.dt,
            100,
            where=(self.df.probability >= CS_TRESHOLD_HIGH) & (self.df.is_night == True),
            facecolor=col_highlight,
            alpha=0.7
        )
        # ax1.fill_between(
        #     self.df.dt,
        #     100,
        #     where=(self.df.probability >= CS_TRESHOLD_LOW) & (self.df.is_night == False),
        #     facecolor=col_med_highlight,
        #     alpha=0.3
        # )

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
            'Wind Speed and Gust\nin km/h',
            color=col_wind,
            # labelpad=15
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
        ax_bar.set_ylim(0, 100)
        ax_bar.set_title(
            'Temperature, DewPoint and Humidity',
            color='white',
        )

        # ---------- Left Axis: Humidity ---------- #

        # ----- Styling ----- #
        ax_bar.tick_params(
            axis='y',
            labelsize='medium',
            labelcolor=col_humidity_text,
        )
        ax_bar.set_ylabel(
            'Humidity in %',
            color=col_humidity_text,
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

        # CS Area ---------- #d
        ax_bar.fill_between(
            self.df.dt,
            100,
            where=(self.df.probability >= CS_TRESHOLD_LOW) & (self.df.is_night == True),
            facecolor=col_highlight,
            alpha=0.4
        )
        ax_bar.fill_between(
            self.df.dt,
            100,
            where=(self.df.probability >= CS_TRESHOLD_LOW) & (self.df.is_night == True),
            facecolor=col_highlight,
            alpha=0.3
        )

        # ax_bar.fill_between(
        #     self.df.dt,
        #     100,
        #     where=(self.df.probability >= CS_TRESHOLD_HIGH) & (self.df.is_night == False),
        #     facecolor=col_med_highlight,
        #     alpha=0.3
        # )
        # ---------- Right Axis: Temperature, Dew Point ---------- #
        ax_temp = axs[1].twinx()

        # ----- Styling ----- #
        ax_temp.tick_params(
            axis='y',
            labelcolor='aqua'
        )
        ax_temp.set_ylabel(
            'Temperature and DewPoint\nin °C',
            color='aqua',
            fontsize=10,
            labelpad=10,
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
        # srise = self.sunrise[0].round('H')
        # sset = self.sunset[0].round('H')

        for ax in axs:
            ax.grid(True)
            # ax.xaxis.set_major_locator(mdates.DayLocator())

            ax.xaxis.set_major_locator(mdates.HourLocator(byhour=[0, 6, 12, 18]))
            ax.xaxis.set_major_formatter(mdates.AutoDateFormatter(mdates.HourLocator(byhour=[0, 6, 12, 18])))  # .DateFormatter('%A'))
            ax.xaxis.set_minor_formatter(mdates.AutoDateFormatter(mdates.AutoDateLocator()))  # DateFormatter('%H:%M'))

            for label in ax.get_xticklabels(minor=False):
                label.set_horizontalalignment('left')

            ax.tick_params(
                axis='x',
                which='major',
                labelsize='small',
                pad=8,
                # labelbottom=True,
                direction='out'
            )
            ax.tick_params(
                axis='x',
                which='minor',
                labelsize='xx-small',
                color='silver',
                grid_color='white',
                grid_alpha=0.5,
                # labelbottom=True,
                pad=2,
            )
        filepath = f'figures/{self.city_name}-{self.run}.png'
        plt.savefig(filepath)  #
        with open(f"data/{self.city_name}-{str(self.run)}.csv", "w") as file:
            self.df.to_csv(file)
        logging.warning(f"weather_data.py: {self.city_name.upper()}: Plot saved.")

    def check_for_changes(self):
        with open(f"data/{self.city_name}-{str(self.run - 1)}.csv") as file:
            last_df = pd.read_csv(file)

        logging.info(f"weather_data.py: \nChecking for changes\n{self.city_name}, Run No: {self.run}")
        logging.info(f"weather_data.py: self.df vs last_df: ")
        # logging.info(self.df.dt[0].dt.strftime("%Y-%m-%d %H:%M"), last_df.dt[0].dt.strftime("%Y-%m-%d %H:%M"))
        last_df.dt = pd.to_datetime(last_df.dt, utc=True)
        last_df = last_df.set_index('dt')
        last_df.index = last_df.index.tz_convert(TIME_ZONE)
        self.df = self.df.set_index('dt')

        logging.info(f"weather_data.py: self.df/last_df of {self.city_name, self.run}")  # \n{self.df}\n{last_df}")
        logging.info(f'weather_data.py: sizes: {self.df.shape, last_df.shape}\n')

        merged = pd.merge(self.df, last_df, how='inner', left_index=True, right_index=True,
                          suffixes=('_new', '_old')).dropna()
        diff_df = pd.DataFrame()
        diff_df['diff'] = abs(merged.probability_new - merged.probability_old)
        diff_df['is_night'] = merged.is_night_new
        diff_df['has_changed'] = [False if merged.is_cs_new[i] == merged.is_cs_old[i] else True for i in merged.index]

        logging.info(f'diff_df:\n{pprint.pformat(diff_df)} for {self.city_name}')

        changed = diff_df.query('diff >= 20 or has_changed == True')
        if changed.shape[0] > 0:
            self.should_alert = True
        else:
            self.should_alert = False

        with open(f'data/diff{self.city_name}-{self.run}.csv', 'w') as f:
            diff_df.to_csv(f)

        # for testing purpose
        # diff_df['diff'] = np.random.randint(0, 50, self.df.shape[0])



# def check_weather():
#     weather = WeatherData()
#     weather.update_weather_data()
#     # Problem with plotting data outside of main func:
#     #  https://stackoverflow.com/questions/34764535/why-cant-matplotlib-plot-in-a-different-thread
#     #weather.plot_data()
#     # weather.check_for_changes()
#     logging.info("__________________END___________________")
#
#
if __name__ == "__main__":
    #     sched.start()
    weather = WeatherData("Stuttgart", 48.7784485, 9.1800132)
    weather.update_weather_data()
    # weather.plot_data()
