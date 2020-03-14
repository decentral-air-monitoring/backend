#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from influxdb import InfluxDBClient
import logging
import csv
from settings import influx_credentials, config

###############################################################################
# InfluxDB
###############################################################################

def model_values(msg):
    """

    :param msg:
    :return:
    """
    statuscode = [int(value) for value in msg.payload.decode('utf-8').split(',')][1]
    is_ok = eval_statuscode(statuscode, msg.payload)


    if is_ok:
        try:
            stationID, _, pm1, pm2_5, pm4, pm10, temperature, humidity, pressure = [int(value) for value in
                                                                                             msg.payload.decode(
                                                                                                 'utf-8').split(',')]
        except ValueError as err:
            logging.error(err.error + "wrong data format")
            return False
        pm1, pm2_5, pm4, pm10, temperature, humidity, pressure = check_illegal_values(pm1, pm2_5, pm4, pm10,
                                                                                      temperature, humidity, pressure)
        return [
            {
                "measurement": "environment",
                "tags": {
                    "stationID": stationID,
                    "statuscode": statuscode,
                    "sensortype": get_sensortype(stationID)
                },
                "fields":{
                    "temperature": temperature,
                    "humidity": humidity,
                    "pressure": pressure
                }
            },
            {
                "measurement": "particles",
                "tags": {
                    "stationID": stationID,
                    "statuscode": statuscode
                },
                "fields":{
                    "pm1": pm1,
                    "pm2_5": pm2_5,
                    "pm4": pm4,
                    "pm10": pm10
                }
            }
        ]
    else:
        return None

def check_illegal_values(pm1, pm2_5, pm4, pm10, temperature, humidity, pressure):
    values = []
    for value in [pm1, pm2_5, pm4, pm10, temperature, humidity, pressure]:
        if value < -300000:
            value = None
        values.append(value)
    return values

def get_sensortype(stationID):
    with open('data/sensors.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        sensors = list(reader)
        found = False
        for sensor in sensors:
            if sensor['stationID'] == str(stationID):
                found = True
                sensortype = config.SENSORS['particle'][sensor['sensortype_particle']]
        if not found:
            logging.error('something went wrong: stationID not in sensors.csv')
            return None
    return sensortype

def eval_statuscode(statuscode, payload):
    """

    :param statuscode:
    :param payload:
    :return:
    """
    if statuscode in [20, 21]:
        return True
    elif statuscode is 30:
        logging.warning(str(payload) + 'status code FAILED: Measurement Failed')
        return False
    elif statuscode is 10:
        logging.info(str(payload) + 'init message received')
        initHandler(payload)
        return False

def initHandler(payload):
    """

    :param payload:
    :return:
    """
    try:
        stationID, _, sensortype_praticle, sensortype_environment, connection_type = [value for value in
                                                                                      payload.decode('utf-8').split(
                                                                                          ',')]
    except ValueError as err:
        logging.error(err.error + "wrong data format")
        return

    sensors = []
    with open('data/sensors.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        sensors = list(reader)
        found = False
        changed = False
        for sensor in sensors:
            if sensor['stationID'] == stationID:
                found = True
                if sensor['sensortype_praticle'] != config.SENSORS:
                    changed = True
                    sensor['sensortype_praticle'] = sensortype_praticle
                if sensor['sensortype_environment'] != sensortype_environment:
                    changed = True
                    sensor['sensortype_environment'] = sensortype_environment
                if sensor['connection_type'] != connection_type:
                    changed = True
                    sensor['connection_type'] = connection_type
        if found is False:
            sensors.append(
                {
                    'stationID': stationID,
                    'statuscode': '30',
                    'sensortype_praticle': sensortype_praticle,
                    'sensortype_environment': sensortype_environment,
                    'connection_type': connection_type
                }
            )

    with open('data/sensors.csv', 'w', newline='') as csvfile:
        fieldnames=['stationID', 'statuscode', 'sensortype_praticle', 'sensortype_environment', 'connection_type']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sensors)

def store_data(sensorData):
    """

    :param sensorData:
    :return:
    """
    influx_client = InfluxDBClient(config.INFLUX_HOST, config.INFLUX_PORT, influx_credentials.USERNAME,
                                influx_credentials.PASSWORD, config.INFLUX_DATABASE)

    if config.INFLUX_DATABASE in (item['name'] for item in influx_client.query('show databases').get_points()):
        logging.info("database already exists")
    else:
        influx_client.create_database(config.INFLUX_DATABASE)

    influx_client.write_points(sensorData)