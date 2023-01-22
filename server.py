from flask import Flask
import json

app = Flask(__name__)

@app.route('/')
def home():
	return 'Hallo!'

@app.route('/get_data')
def get_data():
	with open('files/cs_data.json') as file:
		weather_data = json.load(file)
	return weather_data


if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, debug=True)