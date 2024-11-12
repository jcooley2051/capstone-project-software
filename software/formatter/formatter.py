from datetime import datetime
import json
import paho.mqtt.client as mqtt
import redis

# MQTT setup
broker = "localhost" #IP for broker
port = 1883
topic = "/reading/temp"

# Define connect callback function
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT")
        client.subscribe(topic)  # Subscribe to the topic after connecting
    else:
        print(f"Connection failed with code {rc}")

# Define function to convert the raw temperature reading
def formatTemperature(rawTemperature):
  try:
    temperature = float(rawTemperature)
  except ValueError:
    temperature = -1
  return temperature

# Define message callback function
def on_message(client, userdata, message):
  # Load readings into variables
  rawTemperature = message.payload.decode()

  # Format readings
  formattedTemperature = formatTemperature(rawTemperature)

  # Create a task with the reading
  task = {'type': 'temp', 'value': formattedTemperature, 'flag': False}

  # Add the task to the queue
  r.rpush('task_queue', json.dumps(task))

# Create instance of MQTT client
client = mqtt.Client()

# Assign callback functions
client.on_connect = on_connect
client.on_message = on_message

# Connect to the broker
client.connect(broker, port, 60)

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, db=0)

# Start the MQTT loop to continuously get data
client.loop_forever()
