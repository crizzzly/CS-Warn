from datetime import datetime
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pandas import DateOffset

col_probability = 'mediumvioletred'
col_wind = 'deepskyblue'
col_highlight = 'silver'
#
# def get_onecall_data(type='hourly'):
#     with open('files/weather_data_friday.json') as file:
#         weather_data_all = json.load(file)
#
#     # get date without errors
#     if 'type' == 'hourly':
#         for hour in weather_data_all['hourly']:
#             hour['date'] = datetime.fromtimestamp(hour['dt']+weather_data_all['timezone_offset'])
#         # def get_icon
#         # for moon in df_daily.moon_phase:
#         #     df_daily['moon_phase']
#         df_hourly = pd.DataFrame(weather_data_all['hourly'])
#         df_hourly.set_index('date', drop=False, inplace=True)
#         df_hourly['label'] = df_hourly.dt.date.strftime('%a\n%H:%M')
#         df_hourly['probability'] = 100 - df_hourly.clouds
#         return df_hourly
#
#     elif 'type' == 'daily':
#         for day in weather_data_all['daily']:
#             day['date'] = datetime.fromtimestamp(day['dt']+weather_data_all['timezone_offset'])
#         df_daily = pd.DataFrame(weather_data_all['daily'])
#         df_daily.set_index('date', drop=False, inplace=True)
#         df_daily['label'] = df_daily.date.dt.strftime('%a\n%H:%M')
#         df_daily['probability'] = 100 - df_daily.clouds
#         df_daily['temp'] = [el['night'] for el in df_daily.temp]
#         df_daily['feels_like'] = [el['night'] for el in df_daily.feels_like]
#         return df_daily
#     else:
#         return None

def get_12h_data():
    with open('files/weather_data_12h.json', 'r') as file:
        weather_dat = json.load(file)

    weather_data_len = weather_dat['cnt']
    sunset = weather_dat['city']['sunset']
    sunrise = weather_dat['city']['sunrise']
    weather_data = weather_dat['list']

    weather_df = pd.DataFrame(weather_data)
    weather_df.dt = pd.to_datetime(weather_df.dt, unit='s', origin='unix')
    main = list(weather_df.clouds)    # extract the list of dictionaries
    m_df = pd.DataFrame(main).fillna(0)    # create a new dataframe

    weather = list(weather_df.weather)
    w = [el[0] for el in weather]
    w_df = pd.DataFrame(w).fillna(0)
    weather_df.clouds = m_df['all']

    weather_df['id'] = w_df.id
    weather_df['description'] = w_df.description
    weather_df['icon'] = w_df.icon

    main = list(weather_df.main)
    m_df = pd.DataFrame(main).fillna(0)
    weather_df['temp'] = m_df.temp
    weather_df['temp_min'] = m_df.temp_min
    weather_df['pressure'] = m_df.grnd_level
    weather_df['humidity'] = m_df.humidity
    weather_df['dew_point'] = m_df.temp - ((100 - m_df.humidity) /5 )

    main = list(weather_df['main'])    # extract the list of dictionaries
    m_df = pd.DataFrame(main).fillna(0)    # create a new dataframe
    main = list(weather_df['wind'])    # extract the list of dictionaries
    m_df = pd.DataFrame(main).fillna(0)
    weather_df['wind_speed'] = m_df.speed
    weather_df['wind_gust'] = m_df.gust
    weather_df['wind_deg'] = m_df.deg
    weather_df['probability'] = 100 - weather_df.clouds
    sunsets = []
    sunrises = []
    for i in range(len(weather_df)):
        sunrises.append(pd.Timestamp(sunrise, unit='s') + DateOffset(day=i))
        sunsets.append(pd.Timestamp(sunset, unit='s') + DateOffset(day=i))
    weather_df['sunset'] = sunsets
    weather_df['sunrise'] = sunrise

    return weather_df


def get_peaks(dataframe):
    if dataframe.get('visibility'):
        dataframe.query('@dataframe.probability >= 40 and (@dataframe.dt < @df_daily.sunrise[0] or @dataframe.dt > @df_daily.sunset[0]) ')
    else:
        dataframe.query('@dataframe.probability >= 40 ')
#
# def plot_probability(dataframe):
#     plt.close()
#     plt.style.use('dark_background')
#     plt.figure(figsize=(6, 3),dpi=200)
#     plt.title('CS Probability within the next 48 hours')
#     plt.xticks(fontsize=8, rotation=45)
#     plt.yticks(fontsize=10)
#     plt.ylim(0, 100)
#     plt.xlim(dataframe.dt.min(), dataframe.dt.max())
#
#     ax1 = plt.gca()
#
#     if 'visibility' in dataframe.columns:
#         peaks = dataframe.query('@dataframe.probability >= 40 and (@dataframe.dt < @df_daily.sunrise[0] or @dataframe.dt > @df_daily.sunset[0]) ')
#         plt.title('CS Probability within the next 48 hours')
#         ax1.xaxis.set_major_locator(mdates.DayLocator())
#         ax1.xaxis.set_minor_locator(
#             mdates.HourLocator(
#                 byhour=[
#                     datetime.fromtimestamp(get_onecall_data('daily').sunrise[0]).hour,
#                     datetime.fromtimestamp(get_onecall_data('daily').sunset[0]).hour
#                 ]
#             )
#         )
#         ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a\n%H:%M'))
#     else:
#         plt.title('CS Probability within the next 8 Days')
#         peaks = dataframe.query('@dataframe.probability >= 40 ')
#         ax1.xaxis.set_major_locator(mdates.DayLocator())
#         ax1.xaxis.set_minor_locator(mdates.HourLocator(byhour=[datetime.fromtimestamp(dataframe.dt[0]).hour]))
#         ax1.xaxis.set_major_formatter(mdates.DateFormatter('%a'))
#
#     ax2 = ax1.twinx()
#     ax1.tick_params(axis='y', labelcolor=col_probability)
#
#     ax1.axvspan(
#         xmin=peaks.dt.min(),
#         xmax=peaks.dt.max(),
#         facecolor=col_highlight,
#         alpha=0.5,
#
#     )
#     ax1.plot(dataframe.dt, dataframe.probability, color=col_probability)
#
#     ax1.set_ylabel('Probability in %', color=col_probability, fontsize=10)
#     ax1.set_xlabel('Date')
#
#     ax2.tick_params(axis='y', labelcolor=col_wind)
#     ax2.set_ylabel('Wind speed in km/h', color=col_wind)
#     ax2.plot(dataframe.dt, dataframe.wind_speed, color=col_wind, linestyle='dashed', linewidth=1)
#     plt.show()
#
#
# def plot_temp_humid(df):
#     if 'visibility' in df.columns:
#         title = 'Temperature, Dew Point and Humidity 48 Hours'
#         by_hour = [datetime.fromtimestamp(get_onecall_data('daily').sunrise[0]).hour,
#                    datetime.fromtimestamp(get_onecall_data('daily').sunset[0]).hour]
#         date_format = '%a\n%h:%M'
#     else:
#         title = 'Temperature, Dew Point and Humidity 8 Days'
#         by_hour = [datetime.fromtimestamp(df.dt[0]).hour]
#         date_format = '%a'
#     plt.close()
#     plt.style.use('dark_background')
#
#     plt.figure(figsize=(6, 3), dpi=200)
#     plt.title(title)
#     plt.style.use('dark_background')
#     plt.xticks(fontsize=8, rotation=45)
#     plt.yticks(fontsize=10)
#     plt.xlim(df.date.min(), df.date.max())
#
#     ax1 = plt.gca()
#     ax1.xaxis.set_major_locator(mdates.DayLocator())
#     ax1.xaxis.set_minor_locator(mdates.HourLocator(byhour=by_hour))
#     ax1.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
#
#     ax2 = ax1.twinx()
#     ax1.set_ylabel('Humidity in %', color='mediumblue', fontsize=10)
#     bar = ax1.bar(df.date, df.humidity, color='mediumblue', label='date', alpha=0.5, align='center',
#                   width=10)
#
#     ax2.tick_params(axis='y', labelcolor='aqua')
#     ax2.set_ylabel('Temperature in °C', color='aqua', fontsize=10)
#     ax2.plot(df.date, df.temp, color='aqua', linewidth=1)
#     ax2.plot(df.date, df.dew_point, color='aquamarine', linewidth=1)
#
#     plt.show()

def get_hourly_plot(df_hourly):
    plt.close()
    plt.style.use('dark_background')

    fig, axs = plt.subplots(
        2, 1,
        constrained_layout=True,
        sharex='col',
    )

    ax1 = axs[0]
    ax1.set_xlim(df_hourly.dt.min(), df_hourly.dt.max())
    ax1.set_ylim(0, 100)
    ax1.tick_params(
        axis='y',
        labelcolor=col_probability,
        labelsize='medium',
    )
    ax1.set_title(f'CS Probability within the next {len(df_hourly.index) * 3} hours')
    ax1.set_ylabel('Probability in %', color=col_probability, fontsize=10)
    ax1.fill_between(
        df_hourly.dt,
        100,
        where=df_hourly.probability >= 40,
        facecolor=col_highlight,
        alpha=0.5
    )
    ax1.plot(df_hourly.dt, df_hourly.probability, color=col_probability)

    ax2 = axs[0].twinx()
    ax2.tick_params(axis='y', labelcolor=col_wind, labelsize='medium')
    ax2.set_ylabel('Wind speed in km/h', color=col_wind)
    ax2.plot(df_hourly.dt, df_hourly.wind_speed, color=col_wind, linestyle='dashed', linewidth=1)

    ax_bar = axs[1]
    ax_bar.set_title('Temperature DewPoint and Humidity', color='white')
    ax_bar.set_ylabel('Humidity in %', color='mediumblue', fontsize=10)
    ax_bar.bar(df_hourly.dt, df_hourly.humidity, color='mediumblue', label='date', alpha=0.5, align='center',
                     width=50)
    ax_bar.fill_between(
        df_hourly.dt,
        100,
        where=df_hourly.probability >= 40,
        facecolor=col_highlight,
        alpha=0.5
    )
    ax_temp = axs[1].twinx()

    ax_temp.tick_params(axis='y', labelcolor='aqua')
    ax_temp.set_ylabel('Temperature and DewPoint in °C', color='aqua', fontsize=10)
    ax_temp.plot(df_hourly.dt, df_hourly.temp, color='mediumspringgreen', linewidth=1)
    ax_temp.plot(df_hourly.dt, df_hourly.dew_point, color='aquamarine', linewidth=1, linestyle='dashed')

    hours=[]
    hours.append( pd.Timestamp(df_hourly.sunset[0], unit='s').hour)
    hours.append( pd.Timestamp(df_hourly.sunrise[0], unit='s').hour)
    hours.sort()
    print(hours)
    for ax in axs:
        ax.grid(True)

        ax.xaxis.set_major_locator(mdates.DayLocator())
        ax.xaxis.set_minor_locator(
            mdates.HourLocator(byhour=hours))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%a %H:%M'))

    plt.savefig(f'figures/df_hourly.png')


if __name__ == '__main__':
    df = get_12h_data()
    get_hourly_plot(df)