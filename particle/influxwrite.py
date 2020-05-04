#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from influxdb import InfluxDBClient
import logging
import csv
from datetime import datetime, timedelta
from settings import influx_credentials, config

###############################################################################
# InfluxDB
###############################################################################

def model_values(msg, transport):
    """

    :param msg:
    :return:
    """
    msg_list = get_msg_list(msg)

    if msg_list is None:
        return None
    log_debugging(msg_list, transport)
    statuscode = get_statuscode(msg_list)
    msg_list = complete_message(msg_list, statuscode)
    if msg_list is None:
        return False
    status_ok = eval_statuscode(statuscode, msg_list)
    if status_ok:
        stationID, _, pm1, pm2_5, pm4, pm10, temperature, humidity, pressure = check_illegal_values(msg_list)
        # if statuscode == 20:
        #     if pm1 is not None:
        #         pm1 *= 7.5978
        #         pm1 = int(pm1)
        #     if pm2_5 is not None:
        #         pm2_5 *= 7.2188
        #         pm2_5 = int(pm2_5)
        #     if pm4 is not None:
        #         pm4 *= 7.2193
        #         pm4 = int(pm4)
        #     if pm10 is not None:
        #         pm10 *= 7.2196
        #         pm10 = int(pm10)
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
                    "statuscode": statuscode,
                    "sensortype": get_sensortype(stationID) 
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

def check_illegal_values(msg_list):
    """

    :param msg_list:
    :return:
    """
    values = []
    for value in msg_list:
        if value is not None and value <= -300000:
            value = None
        values.append(value)
    return values

def get_sensortype(stationID):
    """

    :param stationID:
    :return:
    """
    with open('/opt/decentral-air-quality-monitoring-server/particle/data/sensors.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        sensors = list(reader)
        found = False
        for sensor in sensors:
            if sensor['stationID'] == str(stationID):
                found = True
                try:
                    sensortype = config.SENSORS['particle'][int(sensor['sensortype_particle'])]
                except KeyError as err:
                    print(err + "key not in config file")
        if not found:
            logging.error('something went wrong: stationID not in sensors.csv')
            return None
    return sensortype

def eval_statuscode(statuscode, msg_list):
    """

    :param statuscode:
    :param msg_list:
    :return:
    """
    if statuscode in [20, 21]:
        return True
    elif statuscode == 30:
        logging.warning(str(msg_list) + 'status code FAILED: Measurement Failed')
        return False
    elif statuscode == 10:
        logging.info(str(msg_list) + 'init message received')
        initHandler(msg_list)
        return False
    else:
        logging.warning(str(msg_list) + 'unknown status code')
        return False

def initHandler(msg_list):
    """
    :param payload:
    :return:
    """
    stationID, _, sensortype_particle, sensortype_environment, connection_type = check_illegal_values(msg_list)
    sensors = []
    with open('/opt/decentral-air-quality-monitoring-server/particle/data/sensors.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        sensors = list(reader)
        found = False
        for sensor in sensors:
            print(sensor)
            if sensor['stationID'] == str(stationID):
                found = True
                if sensor['sensortype_particle'] != str(config.SENSORS):
                    sensor['sensortype_particle'] = sensortype_particle
                if sensor['sensortype_environment'] != str(sensortype_environment):
                    sensor['sensortype_environment'] = sensortype_environment
                if sensor['connection_type'] != str(connection_type):
                    sensor['connection_type'] = connection_type
        if found is False:
            sensors.append(
                {
                    'stationID': stationID,
                    'statuscode': '10',
                    'sensortype_particle': sensortype_particle,
                    'sensortype_environment': sensortype_environment,
                    'connection_type': connection_type
                }
            )
    with open('/opt/decentral-air-quality-monitoring-server/particle/data/sensors.csv', 'w', newline='') as csvfile:
        fieldnames=['stationID', 'statuscode', 'sensortype_particle', 'sensortype_environment', 'connection_type']
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
        influx_client.write_points([
            {
                "measurement": "environment",
                "tags": {
                    "stationID": "-1",
                    "statuscode": "20",
                    "sensortype": "dummy_sensor"
                },
                "fields":{
                    "temperature": -1,
                    "humidity": -1,
                    "pressure": -1
                }
            },
            {
                "measurement": "particles",
                "tags": {
                    "stationID": "-1",
                    "statuscode": "20",
                    "sensortype": "dummy_sensor"
                },
                "fields":{
                    "pm1": -1,
                    "pm2_5": -1,
                    "pm4": -1,
                    "pm10": -1
                }
            }
        ])
    influx_client.write_points(sensorData)

def complete_message(msg_list, statuscode, transport):
    """

    :param msg_list:
    :param statuscode:
    :return:
    """
    msg_len = len(msg_list)
    if (statuscode == 10 and msg_len == 5) or ( statuscode in [20, 21] and msg_len == 9):
        return msg_list
    elif statuscode not in [10, 20, 21]:
        logging.warning(statuscode + ': is not a valid statuscode')
        log_debugging(msg_list, transport)
        return None
    elif (statuscode == 10 and (msg_len > 5 or msg_len < 2)) or (statuscode in [20, 21] and (msg_len > 9 or
                                                                                             msg_len < 2)):
        logging.warning('message is not in the correct format')
        return None
    msg_incomplete = True
    while(msg_incomplete):
        if statuscode == 10 and msg_len != 5:
            msg_list.append(None)
        elif statuscode in [20, 21] and msg_len != 9:
            msg_list.append(None)
        else:
            msg_incomplete = False
        msg_len = len(msg_list)
    return msg_list

def get_statuscode(msg_list):
    """

    :param msg_list:
    :return:
    """
    try:
        statuscode = msg_list[1]
    except:
        logging.error('could not extract statuscode')
        statuscode = None
    return statuscode

def get_msg_list(msg):
    """

    :param msg:
    :return:
    """
    try:
        msg_list = [int(value) for value in msg.decode('utf-8').split(',')]
    except:
        logging.error('cannot process message')
        msg_list = None
    return msg_list

def log_debugging(msg_list, transport):
    """

    :param msg_list:
    :return:
    """
    sensortype = get_sensortype(msg_list[0])
    if not sensortype:
        sensortype = 'N/A'
    with open('/opt/decentral-air-quality-monitoring-server/particle/data/' + str(msg_list[0]) + '.html',
              'w+') as debugfile:
        debugfile.write("<!DOCTYPE html>\n"
                        "<html>\n"
                        "<body>\n"
                        "<h1>Last Received Message</h1>\n"
                        "<p>Last Message Received: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") +" (UTC)</p>\n"
                        "<p>Message Payload: " + str(msg_list) +"</p>\n"
                        "<p>Registered Sensortype: "+ sensortype +"</p>\n"
                        "<p>Message was sent via: "+ transport +"</p>\n"
                        "</body>\n"
                        "</html>")