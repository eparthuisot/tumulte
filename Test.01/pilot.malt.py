#!/usr/bin/python3

import RPi.GPIO as GPIO
from w1thermsensor import W1ThermSensor
modegpio = GPIO.setmode(GPIO.BOARD)

GPIO.setup(7, GPIO.IN)
GPIO.setup(11, GPIO.OUT)
GPIO.setup(12, GPIO.OUT)
GPIO.setup(13, GPIO.OUT)
GPIO.setup(15, GPIO.OUT)

/*state = GPIO.gpio_function(pin)
print(modegpio)
/*print(state)


for sensor in W1ThermSensor.get_available_sensors():
        print("Sensor %s has temperature %.2f" % (sensor.id, sensor.get_temperature()))
