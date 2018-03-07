#!/bin/bash
# a script to read and save temperature readings from all the group 28 1-wire temperature sensors
#
# get all devices in the '28' family
FILES="ls /sys/bus/w1/devices/w1_bus_master1/ | grep '^28'"
# iterate through all the devices
for file in $FILES
do
	# get the 2 lines of the response from the device
	GETDATA="cat /sys/bus/w1/devices/w1_bus_master1/$file/w1_slave"
	GETDATA1="echo &quot;$GETDATA&quot; | grep crc"
	GETDATA2="echo &quot;$GETDATA&quot; | grep t="
	# get temperature
	TEMP="echo $GETDATA2 | sed -n 's/.*t=//;p'"
	#
	# test if crc is 'YES' and temperature is not -62 or +85
	if [ "echo $GETDATA1 | sed 's/^.*\(...\)$/\1/'" == &quot;YES&quot; -a $TEMP != &quot;-62&quot; -a $TEMP != &quot;85000&quot;  ]
	then
		# crc is 'YES' and temperature is not -62 or +85 - so save result
		echo "date +&quot;%d-%m-%Y %H:%M:%S &quot;; echo $GETDATA2 | sed -n 's/.*t=//;p'" &gt;&gt; /var/1w_files/$file
	else
		# there was an error (crc not 'yes' or invalid temperature)
		# try again after waiting 1 second
		sleep 1
		# get the 2 lines of the response from the device again
		GETDATA="cat /sys/bus/w1/devices/w1_bus_master1/$file/w1_slave"
		GETDATA1="echo &quot;$GETDATA&quot; | grep crc"
		GETDATA2="echo &quot;$GETDATA&quot; | grep t="
		# get the temperature from the new response
		TEMP="echo $GETDATA2 | sed -n 's/.*t=//;p'"
		if [ "echo $GETDATA1 | sed 's/^.*\(...\)$/\1/'" == &quot;YES&quot; -a $TEMP != &quot;-62&quot; -a $TEMP != &quot;85000&quot; ]
		then
			# save result if crc is 'YES' and temperature is not -62 or +85 - if not, just miss it and move on
			echo "date +&quot;%d-%m-%Y %H:%M:%S &quot;; echo $GETDATA2 | sed -n 's/.*t=//;p'" &gt;&gt; /var/1w_files/$file
		fi
		# this is a retry so log the failure - record date/time &amp; device ID
		echo "date +&quot;%d-%m-%Y %H:%M:%S&quot;"quot;"&quot;i - &quot;$file&quot; &gt;&gt; /var/1w_files/err.log
	fi
done
exit 0
