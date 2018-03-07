# --------------------------------------------------------
# PURPOSE: - To monitor temperatures within a backup server's 
#            case and within the garden shed it is running in
#          - To turn on heating or cooling if temperature within
#            server case gets out of a predetermined range    
#          - To log temperatures/times in a tab-delimited file
#            on a NAS box. 

import os
import glob
import time
import datetime
import RPi.GPIO as iO
import os,subprocess
from subprocess import call
from w1thermsensor import W1ThermSensor

#os.system('modprobe w1-gpio')
#os.system('modprobe w1-therm')

# ======================================================================
# Define our subroutines:
# --------------------------------------------------
# Define a function to convert Celsius to Fahrenheit 

def celsiusToFahrenheit(theTempCelsius):
 myTempFarenheit = ((theTempCelsius*9)/5) + 32
 return myTempFarenheit
 
# --------------------------------------------------
# Define a function to get current temperature of the
# Raspberry Pi's CPU  (which, just for grins, we also
# want to monitor)

def getPiCPUtemperature():  
 res = os.popen('vcgencmd measure_temp').readline()  
 return(res.replace("temp=","").replace("'C\n",""))  
 
# --------------------------------------------------
# Define a function fo mount the NAS directory as 
# part of the Pi's file system

# NB: For reasons not yet discovered, using the NAS
#     box's name is not working, so we revert to 
#     it's numeric IP address.
#
#     //Giga2/D  works, no problem, but
#     //NAS/A    fails..... go figure....

def mountNasDirectory():
 myUNC="//10.0.0.8/A"
    
 myCmd = "sudo umount " + myLocalMountDir
 subprocess.Popen(myCmd, shell=True)
 
 myCmd = "sudo mount -t cifs " + myUNC + " " +  myLocalMountDir + " -o  uid=pi,gid=pi,user=admin,pass=xxx"
 subprocess.Popen(myCmd, shell=True)


# ======================================================================
# Perform startup processing: 

# -------------------------------------
# Specify the desired temprature range 
# and time between readings

caseTempDesiredC = int(25)
maxDeviation_BeforeCool = 1.5 
maxDeviation_BeforeHeat = 1.5 
secondsBetweenReadings = 60

# -------------------------------------
# Capture the date we started this script

myDateStamp_Startup =datetime.datetime.now().strftime("%Y-%m-%d")
myDateStamp_Today = myDateStamp_Startup

# -------------------------------------
# Specify NAS box directory in the Pi's
# file system's scheme of things
#
# NB: You might have to read up on this: somehow
#     this directory contains some sort of secret
#     sauce that allows the Pi's OS to populate it
#     with shortcuts to the actual NAS box's 
#     folders... possibly specified in the Samba
#     setup files.

myLocalMountDir="/mnt/NAS_A"
 
# -------------------------------------
# Refer to pins by Broadcom SOC channel
# instead of physical pin#

iO.setmode(iO.BCM)

# -------------------------------------
# Specify which pins are used to flip
# which relay switch on/off and then
# define them as "Output"

relayCool = 10
relayHeat = 11
iO.setwarnings(False)
iO.setup(relayCool, iO.OUT)
iO.setup(relayHeat, iO.OUT)

# -------------------------------------
# Turn off both relay switches - for 
# convenience in testing

iO.output(relayHeat, False)
iO.output(relayCool, False)

# -------------------------------------
# Specify the 3 possible heating/cooling states

tempStateNone = 0
tempStateCool = 1
tempStateHeat = 2 

# -------------------------------------
# Set a pointer to our W1Thermsensor object,
# which will give us easy access to the sensors

mySensor = W1ThermSensor()

# -------------------------------------
# Define sensors by ID (we had to experimentally
# discover these by writing a little script that
# opened the W1ThermSensor class, looped through
# the sensors it knew about and displayed "sensorID"
# for each sensor

sensorID_Case = "0000080222f8"
sensorID_Shed = "04165661cdff"

# -------------------------------------
# Mount the share on the NAS box that we
# will be writing the 2 logs to

mountNasDirectory()

# -------------------------------------
# Open the two tab-delimited log files on the
# NAS box: one for each 24-hour period the
# other cumulative since the last startup.
#
# NB: If either file already exists, we want to
#     open it for Append instead of new albeit 
#     with a blank line to call attention to the
#     fact that log entries were interrupted.
#
# NB: We have sometimes been having trouble with 
#     opening a new file failing w/ErrorCode=2 
#     even so the path is good - only to have
#     it work upon re-starting the script.  This
#     happens if/when somebody on another PC deleted
#     one or both log files while the script is running.

myLogFileDelim = "\t"

myFileHeader1 = myLogFileDelim.join(["\n" + "Temp Desired=" + str(caseTempDesiredC), "maxDeviation Before Cool=" + str(maxDeviation_BeforeCool), "maxDeviation Before Heat=" + str(maxDeviation_BeforeHeat)])
myFileHeader2 = myLogFileDelim.join(["\n" + "TimeStamp", "Case TempC ", "Heat/Cool State", "Shed TempC", "Shed TempF", "Pi CPU TempC"])
#myFileHeader2 = myLogFileDelim.join(["\n" + "TimeStamp", "Case TempC ", "Shed TempC", "Shed TempF", "Pi CPU TempC", "Heat/Cool State  (" + str(tempStateNone) +"=Nothing, " + str(tempStateCool) + "=Cool, " + str(tempStateHeat) + "=Heat)"])

myInterruptIndicator = myLogFileDelim.join(["\n" + "-"*45, "-"*45, "-"*45, "-"*45, "-"*45, "-"*45, "-"*45])

myLogFileSingleDay_Path = myLocalMountDir + "/Mongo_TemperatureLogs/MongoTempLog_SingleDay." + myDateStamp_Today + ".csv"
if os.path.exists(myLogFileSingleDay_Path):
    print("SingleDay: Append to Existing")
    logFileSingleDay = open(myLogFileSingleDay_Path, "a")
    logFileSingleDay.write(myInterruptIndicator)
    logFileSingleDay.write(myFileHeader1)
    logFileSingleDay.write(myFileHeader2)
        
else:   
    print("SingleDay: Create New")
    logFileSingleDay = open(myLogFileSingleDay_Path, "a")
    logFileSingleDay.write(myFileHeader1)
    logFileSingleDay.write(myFileHeader2)


myLogFileCumulative_Path = myLocalMountDir + "/Mongo_TemperatureLogs/MongoTempLog_Cumulative.csv"   
if os.path.exists(myLogFileCumulative_Path):
    print("Cumulative: Append to Existing")
    logFileCumulative = open(myLogFileCumulative_Path, "a")
    logFileCumulative.write(myInterruptIndicator)
    logFileCumulative.write(myFileHeader1)
    logFileCumulative.write(myFileHeader2)
else:   
    print("Cumulative: Create New")
    logFileCumulative = open(myLogFileCumulative_Path, "a")
    logFileCumulative.write(myFileHeader1)
    logFileCumulative.write(myFileHeader2)  
    
# ======================================================================
# Drop into the script's main loop, which keeps on executing until the
# script abends or is cancelled:
#
#    - Reading temp, 
#    - Checking to see if we need heating or cooling, and
#    - Writing temps to the log file

while True:
#   --------------------------------------------
#   See if we need to start a new 24-hour log
#
#   NB: re/"a" vs "w".... Greater Minds have decreed
#       there is no sense in using "w"... because
#       with "a" if the file does not exist, it 
#       gets created same as if we used "w".

    myDateStamp_Current  = datetime.datetime.now().strftime("%Y-%m-%d")
    
    if (myDateStamp_Current != myDateStamp_Today):
        myDateStamp_Today = myDateStamp_Current
        myLogFileSingleDay_Path = myLocalMountDir + "/Mongo_TemperatureLogs/MongoTempLog_SingleDay." + myDateStamp_Today + ".csv"
        logFileSingleDay = open(myLogFileSingleDay_Path, "a")
        logFileSingleDay.write(myFileHeader1)
        logFileSingleDay.write(myFileHeader2)   
        
#   --------------------------------------------
#   Loop through the available sensors (only 2 assumed,
#   for which we experimentally determined their IDs 
#   and hard-coded them into this script)
        
    for mySensor in W1ThermSensor.get_available_sensors():
        curSensorID = mySensor.id
        curTempC = round(float(mySensor.get_temperature()),1)
        myTimeStamp = datetime.datetime.now().strftime("%Y-%m-%d@%H:%M:%S")     

#       ---------------------------------------
#       Identify/assign temp as Case or Shed

        if curSensorID == sensorID_Case:
            myTempCaseC = curTempC
        elif curSensorID == sensorID_Shed:
            myTempShedC = curTempC
        else:
            print("Unexpected SensorID=" + curSensorID)
            
#       ---------------------------------------
#       When we have temps for both inside computer 
#       case and shed, turn heating/cooling on/off
#       accordingly and then write to the 2 logs
#
#       Yes, this will break if/when we do not have
#       both sensors present....

        if curSensorID == sensorID_Shed:
#           ---------------------------------------
#           Turn heating/cooling on/of as needed
          
            if myTempCaseC> (caseTempDesiredC + maxDeviation_BeforeCool):
                iO.output(relayHeat, False)
                iO.output(relayCool, True)
                curTempState = tempStateCool
            elif myTempCaseC < (caseTempDesiredC - maxDeviation_BeforeHeat):
                iO.output(relayCool, False)
                iO.output(relayHeat, True)
                curTempState = tempStateHeat
            else:
                iO.output(relayCool, False)
                iO.output(relayHeat, False)
                curTempState = tempStateNone
                
#           ---------------------------------------
#           Write to the logs, flushing the buffers 
#           of each so we can take a look at the files
#           from another PC even while this script is running
#
#           Why are we getting/logging the Pi's CPU temp?
#           In the immortal words of Alfred E. Neuman "Whyyyyyy not?"
#
#           NB that we check to see if each file is still there
#              and re-create as needed just in case somebody somewhere
#              managed to delete one or both log files at the "right"
#              moment
#
#           NB: The "mountNasDirectiory()" thing is an (unsucessful
#               for now...) attempt to get around mysterious "File 
#               Not Found" errors (Error 02)" if/when somebody on another
#               PC deletes one or both log files while the script is running

            myTempPiC = round(float(getPiCPUtemperature()),1)
            myTempCaseF = round(float(celsiusToFahrenheit(myTempCaseC)))
            myTempShedF = round(float(celsiusToFahrenheit(myTempShedC)))
            myLogFileLine = myLogFileDelim.join(["\n" + myTimeStamp, str(myTempCaseC), str(curTempState), str(myTempShedC), str(myTempShedF), str(myTempPiC)])
                        
            if os.path.exists(myLogFileSingleDay_Path):
                logFileSingleDay = open(myLogFileSingleDay_Path, "a")
                logFileSingleDay.write(myLogFileLine)
                logFileSingleDay.close
            else:   
                myLogFileSingleDay_Path = myLocalMountDir + "/Mongo_TemperatureLogs/MongoTempLog_SingleDay." + myDateStamp_Startup + ".csv"             
                mountNasDirectory()
                logFileSingleDay = open(myLogFileSingleDay_Path, "a")                   
                logFileSingleDay.write(myFileHeader1)
                logFileSingleDay.write(myFileHeader2)   
                logFileSingleDay.write(myLogFileLine)
                logFileSingleDay.close      
                                                
            if os.path.exists(myLogFileCumulative_Path):
                logFileCumulative = open(myLogFileCumulative_Path, "a")             
                logFileCumulative.write(myLogFileLine)
                logFileCumulative.close
            else:
                mountNasDirectory() 
                logFileCumulative = open(myLogFileCumulative_Path, "a")                 
                logFileCumulative.write(myFileHeader1)
                logFileCumulative.write(myFileHeader2)          
                logFileCumulative.write(myLogFileLine)
                logFileCumulative.close

#           -------------------------------------
#           Just for testing/debugging, print some
#           info on the console

            print("ServerCase=" + str(myTempCaseC) + "C / " + str(myTempCaseF) + "F  Shed=" + str(myTempShedC) + "C / " + str(myTempShedF) + "F   TempState=" + str(curTempState) + "   PiCPU=" + str(myTempPiC) + " at " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")) 
   
    time.sleep(secondsBetweenReadings)
#   sys.exit

