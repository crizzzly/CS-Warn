import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
import api_talk

FROM_FILE = True
TIME_ZONE = 'Europe/Berlin'
LABEL_FONTSIZE = 10
TICKLABEL_SIZE_Y = 'medium'
TICKLABEL_SIZE_X = 'xx-small'

CS_TRESHOLD = 50

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
        self.plot_title = ''
        self.sunset = None  #[]
        self.sunrise = None
        self.tz_offset = 0
        self.ids = []
        self.icons = []
        self.probabilities = []

    def update_weather_data(self):
        """
        gets OWM Weather Data via api_talk.py
        saves current weather
        processes data for analysis and plotting via pandas

        input: t = 'one_call' / '5d' for one_call(48h or 8d) or 5d (every 3h) forecast
        """

        if self.type == '5d':  # !! Only in 3h-Steps available
            json_file = 'files/weather_data_5d.json'
            call_api = api_talk.get_5d_forecast
            self.plot_title = f'CS Probability within the next {5 * 24} hours'
        # owm_data_key = ['list']
        # elif self.t == 'one_call':
        else:
            json_file = 'files/weather_data_onecall.json'
            call_api = api_talk.get_onecall_forecast
            self.plot_title = f'CS Probability within the next {2 * 24} hours'
            # owm_data_key = ['hourly', 'daily']

        # Get WeatherData
        if FROM_FILE:
            with open(json_file) as file:
                data = json.load(file)
        else:
            with open(json_file, 'w') as file:
                data = call_api()
                file.write(json.dumps(data))

        # ----------- for 5d forecast: ----------- #
        if self.type == '5d':
            self.df = pd.DataFrame(data['list'])
            self.tz_offset = data['city']['timezone']

            # sunrise and sunset
            # Convert UTC Timestamps to pd.datetime
            sunrise = pd.to_datetime(data['city']['sunrise'], unit='s', origin='unix', utc=True)
            sunset = pd.to_datetime(data['city']['sunset'], unit='s', origin='unix', utc=True)

            # Convert to local timezone
            self.sunrise = sunrise.tz_convert(TIME_ZONE)
            self.sunset = sunset.tz_convert(TIME_ZONE)

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
            print(f'wind_speed: {self.df.wind_speed}')

        else:  # onecall_api
            self.df = pd.DataFrame(data['hourly'])
            df_daily = pd.DataFrame(data['daily'])
            self.tz_offset = data['timezone_offset']

            # Sunrise and set
            # Convert UTC Timestamps to pd.datetime
            df_daily.dt = pd.to_datetime(df_daily.dt, utc=True, unit='s', origin='unix')
            df_daily.sunrise = pd.to_datetime(df_daily.sunrise, utc=True, unit='s', origin='unix')
            df_daily.sunset = pd.to_datetime(df_daily.sunset, utc=True, unit='s', origin='unix')

            # Convert to local timezone
            df_daily.dt = df_daily.dt.dt.tz_convert(TIME_ZONE)
            df_daily.sunrise = df_daily.sunrise.dt.tz_convert(TIME_ZONE)
            df_daily.sunset = df_daily.sunset.dt.tz_convert(TIME_ZONE)
            self.sunrise = df_daily.sunrise[0]
            self.sunset = df_daily.sunset[0]

            # self.df.sunrise = df_daily.sunrise
            # self.df.sunset = df_daily.sunset
            # print('onecall index & columns:')
            # print(self.df.index)
            # print(self.df.columns)

        # ----------- for 5d & onecall: ----------- #
        # convert dt from int to timeseries/timestamps
        self.df.dt = pd.to_datetime(self.df.dt, unit='s', origin='unix', utc=True)
        self.df.dt = self.df.dt.dt.tz_convert(TIME_ZONE)

        # to easily check if time is at night
        self.df['is_night'] = [
            True if self.df.dt[i].time() < self.sunrise.time() or self.sunset.time() < self.df.dt[i].time() else False
            for i in self.df.index
        ]

        # one column for CS Probability per timestamp
        self.df['probability'] = 100 - self.df.clouds

        self.df['is_cs'] = [
            True if self.df.probability[i] > CS_TRESHOLD and self.df.is_night[i] == True else False
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
            self.plot_title
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
            where=(self.df.probability >= 40) & (self.df.is_night == True),
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
            where=(self.df.probability >= 40) & (self.df.is_night == True),
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
        minor_labels = [self.sunrise.hour, self.sunset.hour]
        print(f"sunrise/set: {self.sunrise, self.sunset}")
        print(f'minor labels: {minor_labels}')
        minor_labels.sort()

        for ax in axs:
            ax.grid(True)
            ax.xaxis.set_major_locator(mdates.DayLocator())

            ax.xaxis.set_minor_locator(mdates.HourLocator(byhour=[6, 12, 18]))
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%A'))
            ax.xaxis.set_minor_formatter(mdates.DateFormatter('%H:%M'))

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

        plt.savefig(f'figures/{self.type}.png')#

    def check_for_changes(self):
        dataset = self.df[['dt', 'probability', 'is_cs']].set_index('dt')
        last_df = pd.read_json("data/weather_df.json")
        last_df.index = pd.to_datetime(last_df.index, utc=True)
        last_df.index = last_df.index.tz_convert(TIME_ZONE)
        dataset.to_json("data/weather_df.json")

        dataset, last_df = dataset.align(last_df, axis=0, join="inner")
        dataset['diff'] = abs(dataset.probability - last_df.probability)

        # for testing purpose
        # dataset['diff'] = np.random.randint(0, 50, dataset.shape[0])

        print(dataset)
        print(last_df)
        print(last_df.size)

        change_val = 25
        significant_changes = dataset.query("diff >= @change_val and is_cs == True")
        print(f'changes: {significant_changes.any()}')
        print(significant_changes)
        print(significant_changes.size)


if __name__ == '__main__':
    weather = WeatherData()
    weather.update_weather_data()
    weather.plot_data()
    weather.check_for_changes()
