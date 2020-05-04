#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import paho.mqtt.client as mqtt
import logging
logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename='/var/log/particle/particle.log',
                    level=logging.INFO)
from influxwrite import model_values, store_data
from settings import mqtt_credentials, config


###############################################################################
#   mqtt callback functions
###############################################################################


def on_connect(client, userdata, flags, rc):
    """
    The callback function for when the client receives a CONNACK response
    from the server.
    :param client: mqtt client object
    :param userdata: userdata transmitted when connecting to the mqtt broker
    :param flags: flags used when connecting to the mqtt broker
    :param rc: connction status code
    :return: nothing
    """
    logging.info("Connected with result code " + str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe(config.MQTT_TOPIC)
    logging.info("subscribing to topic " * str(config.MQTT_TOPIC))


def on_message(client, userdata, msg):
    """
    The callback function for when a PUBLISH message is received from the server.
    :param client: mqtt client object
    :param userdata: userdata transmitted when publishing a mqtt message
    :param msg: {topic, payload} containing received mqtt message payload and topic
    :return: nothing
    """
    global model_values
    global store_data
    global logging
    try:
        print(msg.topic+" "+str(msg.payload))
        sensorData = model_values(msg.payload, transport="WLAN")
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
# Pass credentials to the client object to authenticate to the mqtt broker
client.username_pw_set(username=mqtt_credentials.USERNAME,
                       password=mqtt_credentials.PASSWORD)
# Connect to the mqtt broker with parameters specified in the config file with
client.connect(host=config.MQTT_HOST, port=config.MQTT_PORT,
               keepalive=config.MQTT_KEEPALIVE)
# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.
client.loop_forever()
