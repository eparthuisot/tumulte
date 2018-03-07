#!/usr/bin/python3
# -*- coding: utf-8 -*-
#####################################################
## lecture de sondes de temperature 1-wire DS18B20 ##
##                                                 ##
## lancement : sudo python ...                     ##
#####################################################
 
import time
import RPi.GPIO as GPIO
import pigpio as pi
from influxdb import InfluxDBClient
from os import system

#Definition liste vitesse venilateur
#list_fan_speed = ['1.0.0.0_86','0.1.0.0_80','1.1.0.0_75','0.0.1.0_70','1.0.1.0_65','0.1.1.0_60','1.1.1.0_50','0.0.0.1_40','1.0.0.1_30','0.1.0.1_25','1.1.1.1_00']
dict_fan_speed = {"85":"1.0.0.0",
                  "80":"0.1.0.0",
                  "75":"1.1.0.0",
                  "70":"0.0.1.0",
                  "65":"1.0.1.0",
                  "60":"0.1.1.0",
                  "50":"1.1.1.0",
                  "40":"0.0.0.1",
                  "30":"1.0.0.1",
                  "25":"0.1.0.1",
                  "00":"1.1.1.1",
                 }
dict_heating_value = {"0":"0.0.0",
                      "1":"1.0.0",
                      "2":"1.1.0",
                      "3":"1.1.1",
                     }

dict_gpio_fan_speed = {0:"11",1:"12",2:"13",3:"15"} ## Brochage gpio pour relais gestion vitesse ventilo
dict_gpio_heating_relay = {0:"29",1:"31",2:"33"}   ## Brochage gpio pour les relais de résistance. Forcer ventilateur si allumage resistance

## Initialisation GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)

## Configuration borne GPIO modulateur ventilateur
chan_fan_list = [11,12,13,15]
GPIO.setup(chan_fan_list, GPIO.OUT)

## Configuration borne GPIO modulateur ventilateur
chan_heating_list = [29,31,33]
GPIO.setup(chan_heating_list, GPIO.OUT)

## function to managed fan speed
def fan_speed(ValueFs):
  CountGpio = 0
  Matrix_Fan_Speed = dict_fan_speed[ValueFs]
  for ValuePin in Matrix_Fan_Speed:
    GpioPin = dict_gpio_fan_speed[CountGpio]
    if str(ValuePin) != ".":
      #print (ValuePin)
      #print (GpioPin)
      #print (CountGpio)
      if ValuePin == "1":
        GPIO.output(int(GpioPin), GPIO.HIGH)
        #print (ValuePin,GpioPin)
      else:
        GPIO.output(int(GpioPin), GPIO.LOW)
        #print (ValuePin,GpioPin)
      CountGpio=CountGpio+1

## function to managed heating
def heating_turn_on(ValueHeating):
  CountGpio = 0
  Matrix_Heating_Value = dict_heating_value[ValueHeating]
  for ValuePin in Matrix_Heating_Value:
    GpioPin = dict_gpio_heating_relay[CountGpio]
    if str(ValuePin) != ".":
      #print (ValuePin)
      #print (GpioPin)
      #print (CountGpio)
      if ValuePin == "1":
        GPIO.output(int(GpioPin), GPIO.HIGH)
        #print (ValuePin,GpioPin)
      else:
        GPIO.output(int(GpioPin), GPIO.LOW)
        #print (ValuePin,GpioPin)
      CountGpio=CountGpio+1

## module GPIO 1-wire et capteur de temperature #####
system('modprobe w1-gpio')
system('modprobe w1-therm')
 
## chemin vers les sondes ###########################
base_dir = '/sys/bus/w1/devices/'
 
## Remplacez les repertoires 28-xxxxxxxxxxx #########
## par vos propres repertoires . ####################
## Et si vous avez un nombre de sonde different #####
## supprimer (ou ajouter) les lignes ci dessous #####
sonde1 = "/sys/bus/w1/devices/w1_bus_master1/28-041780c05dff/w1_slave"
sonde2 = "/sys/bus/w1/devices/w1_bus_master1/28-041780ced3ff/w1_slave"
## et ajuster aussi les 2 lignes ci dessous #########
sondes = [sonde1, sonde2]
sonde_value = [0, 0]
 
## fonction ouverture et lecture d'un fichier #######
def lire_fichier(fichier):
    f = open(fichier, 'r')
    lignes = f.readlines()
    f.close()
    return lignes
 
## code principal ###################################
for (i, sonde) in enumerate(sondes):
    lignes = lire_fichier(sonde)
    while lignes[0].strip()[-3:] != 'YES': # lit les 3 derniers char de la ligne 0 et recommence si pas YES
        sleep(0.2)
        lignes = lire_fichier(sonde)
 
    temp_raw = lignes[1].split("=")[1] # quand on a eu YES, on lit la temp apres le signe = sur la ligne 1
    sonde_value[i] = round(int(temp_raw) / 1000.0, 2) # le 2 arrondi a 2 chiffres apres la virgule

    json_body = [
                {"measurement": "temperature",
                 "tags": {"host": "rasp01.tumulte","zone": i },
                 #"time": time.strftime('%Y-%m-%d %H:%M:%S'),"fields": {"value": sonde_value[i]}
                 "fields": {"value": sonde_value[i]}
                }
                ]
    client = InfluxDBClient('localhost', 8086, 'root' , 'root' , 'datasensor_tumulte')
    client.write_points(json_body)
    client.close()

    #result = client.query('select value from temperature;')
    #print("Result: {0}".format(result))

    print ("sonde",i,"=",sonde_value[i]) # affichage a l'ecran

FanSpeed = input ("Vitesse souhaitée:")
ValueExistF = FanSpeed in dict_fan_speed
if ValueExistF:
  FanSpeedC = fan_speed (FanSpeed)
  json_body = [
    {"measurement": "speed_fan",
    "tags": {"host": "rasp01.tumulte"},
    "fields": {"value": FanSpeed}
    }]
  client = InfluxDBClient('localhost', 8086, 'root' , 'root' , 'datasensor_tumulte')
  client.write_points(json_body)
  client.close()
else:
  print("Value speed false")

HeatingValue = input ("Valeur nombre résistance:")
ValueExistH = HeatingValue in dict_heating_value
if ValueExistH:
  HeatingValueC = heating_turn_on (HeatingValue)
  json_body = [
    {"measurement": "heating_value",
    "tags": {"host": "rasp01.tumulte"},
    "fields": {"value": HeatingValue}
    }]
  client = InfluxDBClient('localhost', 8086, 'root' , 'root' , 'datasensor_tumulte')
  client.write_points(json_body)
  client.close()
else:
  print("Value heating false")

def read_gpio(ValueHeating):
  CountGpio = 0
  Matrix_Heating_Value = dict_heating_value[ValueHeating]
  for ValuePin in Matrix_Heating_Value:
    GpioPin = dict_gpio_heating_relay[CountGpio]
    if str(ValuePin) != ".":
      #print (ValuePin)
      #print (GpioPin)
      #print (CountGpio)
      if ValuePin == "1":
        pi.set_pull_up_down(int(GpioPin), pigpio.PUD_UP)
        #print (ValuePin,GpioPin)
      else:
        pi.set_pull_up_down(int(GpioPin), pigpio.PUD_DOWN)
        #print (ValuePin,GpioPin)
      print(pi.read(int(GpioPin)))
      CountGpio=CountGpio+1

read_gpio(HeatingValue)
