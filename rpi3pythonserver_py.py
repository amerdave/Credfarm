"""

This is the Flask Server, run on anything with Python3.
I've marked the points you need to edit if you want to add a new device or functionality.
Dont forget to add your Slack token on line 128

"""



from slacker import Slacker
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from flask import Flask, jsonify, abort, make_response, request, url_for
import forecastio

# Note: if you see '# Add new device here(X)'
# This is where you copy the syntax directly above to add a new device
# There are 6 points in total.

# Darksky weather info
# Go to https://darksky.net/dev and register
# Google your lat and long
api_key = "<API KEY>"
lat = 51.76524
lng = -10.16642

scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']

def gAuth():
        global credentials, gc, wemosd1worksheet,
        nodemcu_1worksheet, nodemcu_2worksheet
        # Add new device here(1)
        
        credentials = ServiceAccountCredentials.from_json_keyfile_name('clientsecret.json', scope)
        
        # Authorise with Google
        gc = gspread.authorize(credentials) 
        # Open the wemosd1 worksheet
        wemosd1worksheet = gc.open("gsheet").get_worksheet(0) 
        # Open the nodemcu_1 worksheet
        nodemcu_1worksheet = gc.open("gsheet").get_worksheet(1) 
        # Open the nodemcu_2 worksheet
        nodemcu_2worksheet = gc.open("gsheet").get_worksheet(2)
        
        # Add new device here(2)


gAuth()

# Delete Old Values
wemosd1worksheet.clear() 
nodemcu_1worksheet.clear()
nodemcu_2worksheet.clear()

# Add new device here(3)

# Add column names to empty spreadsheet
wemosd1worksheet.append_row(['Time', 'Soil Moisture %'], value_input_option='RAW') 
nodemcu_1worksheet.append_row(['Time', 'Light %', 'Temp *C', 'Humid %RH'], value_input_option='RAW')
nodemcu_2worksheet.append_row(['Time', 'Tank Water Level'], value_input_option='RAW')

# Add new device here(4)


app = Flask(__name__)

# Declare variables that you want to pass between devices.
smlevel = 0

# Think of these as containers for mPy sensor data.
wemosd1_readings = [
    {
        'DataPoint': 1,
        'LevelValue': u'WaterLevelReadings:',
        'Done': False
    }
]

nodemcu_1_readings = [
    {
        'DataPoint': 1,
        'LightValue': u'LightLevelReadings:',
        'TempValue': u'TempLevelReadings:',
        'HumidValue': u'HumidLevelReadings:',
        'Done': False
    }
]

nodemcu_2_readings = [
	{
        'DataPoint': 1,
        'Value': u'SoilMoistureReadings:',
        'Done': False
    }
]

soilmoisture_readings = [
	{
        'DataPoint': 1,
        'Value': u'SoilMoistureReadings:',
        'Done': False
    }
]

# Add new device here(5)

# The following 3 '@app.route' are examples of how to use GET requests
# from your mPy devices to contact API's and get sensor data from 
# the other nodes. This is where you add functionality.

@app.route('/darksky', methods=['GET'])
def darksky():
    forecast = forecastio.load_forecast(api_key, lat, lng)
    byHour = forecast.hourly()
    data = []
    for hourlyData in byHour.data:
        data.append(hourlyData.precipProbability)
    data = data[:23]
    sum = 0
    for item in data:
        sum += float(item)

    OverallProb = str(round(sum / (float(len(data) / 100)), 3))
	
    return jsonify({'ChanceOfRainToday % ':OverallProb, 'Data':data}), 201

@app.route('/soilmoisture', methods=['GET'])
# Return the Soil Moisture Level to the Pump Controller when requested
def sendSoilMoisture():
    global smlevel
    return jsonify({'SoilMoistureLevel':smlevel}), 201

@app.route('/tankalert', methods=['GET'])
# Sending a Push notification example
def Push():
    # Replace with your Slack token
    slack_token = "xoxp-66666666666-66666666666-66666666666-83d588fb45145363f4015785a6ebf3f02"
    slack_channel = "#alerts"
    slack_msg = "Tank Level Alert, You must refill before pumping can continue."
    slack = Slacker(slack_token)
    
    # Send Push Notification
    slack.chat.post_message(slack_channel, slack_msg, '<slack user>') 
    return jsonify({'Status':'Push Notification sent'}), 201

# The following 3 '@app.route' are examples of containers which receive JSON 
# sensor data in a POST request, extract data and append to Google Sheet

@app.route('/nodemcu_1', methods=['POST'])
def ENV_reading():
    if not request.json or 'Done' in request.json == True:
        abort(400)
    reading = {
        'DataPoint': nodemcu_1_readings[-1]['DataPoint'] + 1,
        'LightValue': request.json.get('Light', ""),
        'TempValue': request.json.get('Temp', ""),
        'HumidValue': request.json.get('Humid', ""),
        'Time': request.json.get('Time', ""),
        'Done': False
    }
    nodemcu_1_readings.append(reading)
    Lightvariable = str(request.json.get('Light', ""))
    Tempvariable = str(request.json.get('Temp', ""))
    Humidvariable = str(request.json.get('Humid', ""))

    nodemcu_1worksheet.append_row([request.json.get('Time', ""), Lightvariable, Tempvariable, Humidvariable], value_input_option='RAW')
    
    return jsonify({'reading': reading}), 201
    
# NOTE on /nodemcu_2:
# The soil moisture level which the pump contoller can request 
# is saved to a global variable, smlevel in the /nodemcu_2 '@app.route'.
# This is an example of how to pass sensor values between different MCU's

@app.route('/nodemcu_2', methods=['POST'])
def create_reading():
    global smlevel
    if not request.json or 'Done' in request.json == True:
        abort(400)
    reading = {
        'DataPoint': wemosd1_readings[-1]['DataPoint'] + 1,
        'Value': request.json.get('Value', ""),
        'Time': request.json.get('Time', ""),
        'Done': False
    }
    wemosd1_readings.append(reading)
    variable = request.json.get('Value')
    smlevel = variable
    if float(variable) > 100:
        variable = 100.00
    if float(variable) < 0:
        variable = 0.00

    wemosd1worksheet.append_row([request.json.get('Time', ""), str(request.json.get('Value', ""))], value_input_option='RAW')
    
    return jsonify({'reading': reading}), 201

	
@app.route('/wemosd1', methods=['POST'])
def LEVEL_reading():
    if not request.json or 'Done' in request.json == True:
        abort(400)
    reading = {
        'DataPoint': nodemcu_2_readings[-1]['DataPoint'] + 1,
        'Level': request.json.get('Level', ""),        
        'Time': request.json.get('Time', ""),
        'Done': False
    }
    nodemcu_2_readings.append(reading)
    Levelvariable = str(request.json.get('Level', ""))

    nodemcu_2worksheet.append_row([request.json.get('Time', ""), Levelvariable], value_input_option='RAW')
    
    return jsonify({'reading': reading}), 201


# Add new device here(6)

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def not_found(error):
    return make_response(jsonify({'error': 'The request could not be understood by the server due to malformed syntax.'}), 400)

@app.errorhandler(500)
def NotAuth(error):
    gAuth()
    return make_response(jsonify({'error': 'Not Authorised. Reauthorising...'}), 500)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=False, threaded=True)
