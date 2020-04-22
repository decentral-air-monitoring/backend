################
# LOCAL MQTT
################

# specify the hostname/ip of the mqtt broker
MQTT_HOST = "particle.nodelove.eu"
# specify the server port on which the mqtt broker is listening
MQTT_PORT = 8883
MQTT_KEEPALIVE = 60
# sepcify the topic to subscribe to
MQTT_TOPIC = "particle/#"


########################
# The Thins Network MQTT
########################

# specify the hostname/ip of the mqtt broker
TTN_MQTT_HOST = "eu.thethings.network"
# specify the server port on which the mqtt broker is listening
TTN_MQTT_PORT = 8883
TTN_MQTT_KEEPALIVE = 60
# sepcify the topic to subscribe to
TTN_MQTT_TOPIC = "+/devices/+/up"

############
# InfluxDB
############

# hostname or IP adress of the influx server
INFLUX_HOST = "localhost"
# influx listening port
INFLUX_PORT = 8086
# influx database name
INFLUX_DATABASE = 'sensordata'

############
# Sensors
############

# Protocol specific codes for the different sensor types that are currently supported
SENSORS = {
    "particle":{
        0: "NoSensor",
        1: "DemoSensor",
        2: "SDS011",
        3: "HMPA115C0",
        4: "SPS30"
    },
    "environment":{
        0: "NoSensor",
        1: "BME680"
    }
}

####################
# Connection Type
####################

# Protocol specific codes to specify how the station connects to the backend
CONNECTION = {
    0: "NotSet",
    1: "LoraOnly",
    2: "WifiOnly",
    3: "LoraAndWifi"
}