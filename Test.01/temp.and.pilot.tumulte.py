#!/usr/bin/python3
# -*- coding: utf-8 -*-
#####################################################
## lecture de sondes de temperature 1-wire DS18B20 ##
##                                                 ##
## lancement : sudo python ...                     ##
#####################################################
 
from os import system
import time
from influxdb import InfluxDBClient
 
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
    client = InfluxDBClient('localhost', 8086, 'root' , 'root' , 'temperature_tumulte')
    client.write_points(json_body)
    #client.close()

    #result = client.query('select value from temperature;')  #query to influxdb
    #print("Result: {0}".format(result))  #view result of query

     
    print ("sonde",i,"=",sonde_value[i]) # affichage a l'ecran
