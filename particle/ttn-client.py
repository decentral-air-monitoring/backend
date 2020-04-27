import paho.mqtt.client as mqtt
import logging
import json
import base64

from influxwrite import model_values, store_data
from settings import config, influx_credentials, ttn_credentials
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename='/var/log/particle/ttn_particle.log',
                    level=logging.INFO)

def on_connect(client, userdata, flags, rc):

  logging.info("Connected with result code " + str(rc))

  # Subscribing in on_connect() means that if we lose the connection and
  # reconnect then subscriptions will be renewed.
  client.subscribe(config.TTN_MQTT_TOPIC)
  logging.info("subscribing to topic " * str(config.TTN_MQTT_TOPIC))


def on_message(client, userdata, msg):
  """
  The callback for when a PUBLISH message is received from the server.
  :param client:
  :param userdata:
  :param msg: object containing received mqtt message
  :return: nothing
  """
  global model_values
  global store_data
  global logging
  try:
    print(msg.topic + " " + base64.b64decode(json.loads(msg.payload)['payload_raw']).decode('utf8'))
    sensorData = model_values(base64.b64decode(json.loads(msg.payload)['payload_raw']))
    if sensorData:
      store_data(sensorData)
      logging.info(str(msg.payload) + 'successfully stored to influxdb')
  except Exception as e:
    print(e)
    logging.warning(str(msg.payload) + 'error storing data to influxdb: ' + str(e))

###############################################################################
#   mqtt client configuration
###############################################################################

# Create Client Object
client = mqtt.Client()

# Execute on_connect function in case of client event: on_connect
client.on_connect = on_connect
# Execute on_message function in case of client event: on_message
client.on_message = on_message
# Make TLS configuration (using default values)
client.tls_set()
#
client.username_pw_set(username=ttn_credentials.APP_ID,
                       password=ttn_credentials.ACCESS_KEY)
client.connect(host=config.TTN_MQTT_HOST, port=config.TTN_MQTT_PORT,
               keepalive=config.TTN_MQTT_KEEPALIVE)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()