"""
VISA Control: FastFrame Summary Frame Transfer
Author: Morgan Allison
Date Created: 6/2014
Date Edited: 2/2016
This program acquires 10 instances of a pulse train that contains a 
periodic runt using FastFrame and transfers the summary frame to the computer.
Windows 7 64-bit, NI-VISA 5.4
Python 2.7.9 64-bit (Anaconda 3.7.0)
To get Anaconda: http://continuum.io/downloads
PyVISA 1.5, NumPy 1.8.1, and MatPlotLib 1.3.1
Tested on Tested on DPO5204B, MSO72004, and DPO7104C
"""

import visa
import numpy
import matplotlib.pyplot as plt
from struct import unpack

"""#################SEARCH/CONNECT#################"""
#establish communication with scope
rm = visa.ResourceManager()
inst = rm.open_resource('TCPIP::192.168.1.10::INSTR')
inst.timeout = 10000
print(inst.ask('*idn?'))
inst.write('*rst')
inst.ask('system:error:all?')


"""#################INITIALIZE VARIABLES#################"""
#variables for individual settings
horizscale = '200e-9'      #sec/div
samplerate = '2.5e9'       #S/sec
numberofframes = 10
voltsperdiv = .5
position = -3
highthresh = 2
lowthresh = 0.75


"""#################CONFIGURE INSTRUMENT#################"""
#scope setup
inst.write('acquire:state 0')                                     #turn off the acquisition system
inst.write('horizontal:mode auto')                                #set horizontal settings to auto
inst.write('horizontal:mode:scale {0}'.format(horizscale))        #set horiztonal scale
inst.write('horizontal:mode:samplerate {0}'.format(samplerate))   #set sample rate
inst.write('acquire:mode sample')                                 #set acquire mode to sample
inst.write('horizontal:fastframe:state 1')                        #turn on FastFrame
inst.write('horizontal:fastframe:count {0}'.format(numberofframes))   #specify number of frames
inst.write('ch1:scale {0}'.format(voltsperdiv))                       #set vertical scale
inst.write('ch1:position {0}'.format(position))                       #set vertical position
inst.write('trigger:a:type pulse')                                #set trigger type to pulse
inst.write('trigger:a:pulse:class runt')                          #set pulse class to runt
inst.write('trigger:a:pulse:runt:qualify occurs')                 #set trigger upon occurrence of a runt
inst.write('trigger:a:pulse:runt:polarity:ch1 positive')          #set runt trigger polarity
inst.write('trigger:a:pulse:runt:threshold:high {0}'.format(highthresh))#set the high and low runt thresholds
inst.write('trigger:a:pulse:runt:threshold:low {0}'.format(lowthresh))
print('Horizontal, vertical, and trigger settings configured.')

#configure data transfer settings
inst.write('header 0')                    #turn the header off
inst.write('horizontal:fastframe:sumframe average') #tell the scope to create a summary frame that is the average of all frames
inst.write('data:encdg fastest')          #set encoding type to fast binary
inst.write('data:source ch1')             #set data source
inst.write('data:stop 100000')            #set end of record
inst.write('wfmoutpre:byt_n 1')           #set number of bytes per data point
inst.write('data:framestart 11')          #as long as start/stop frames are greater than the total number of frames,
inst.write('data:framestop 12')           #the program will only capture the last frame, which is the summary frame, which is what we want
print('Data transfer settings configured.')


"""#################ACQUIRE/PROCESS DATA#################"""
print('Acquiring waveform.')
#inst.Timeout = 60                        #increase timeout in order to capture all frames
inst.write('acquire:stopafter sequence')  #set scope to single acquisition mode
inst.write('acquire:state 1')             #start acquisition
inst.ask('*opc?')                         #wait until scope has finished acquiring waveforms
print('Waveform acquired.\n')


#Retrieve vertical and horizontal scaling information
#because the returned values are strings, we need to convert to
#numerical data types in order to use them to scale, thus the typecasting

#Vertical
#yoffset is unscaled offset data that is set by the ch<x>:offset
yoffset = float(inst.ask('wfmoutpre:yoff?'))
#ymult is the scaling factor that is set by ch<x>:scale
ymult = float(inst.ask('wfmoutpre:ymult?'))
#yzero is scaled position data that is set by ch<x>:position
yzero = float(inst.ask('wfmoutpre:yzero?'))
#print(yoffset, ymult, yzero)

#Horizontal
#number of points in the waveform acquisition
numberofpoints = int(inst.ask('wfmoutpre:nr_pt?'))
#amount of time between data points
xincrement = float(inst.ask('wfmoutpre:xincr?'))
#absolute time value of the beginning of the waveform record
xzero = float(inst.ask('wfmoutpre:xzero?'))
#print(numberofpoints, xincrement, xzero)

inst.write('curve?')          #send curve? query
print('Curve query sent.')

rawdata = inst.read_raw()     #Read all the raw data from the scope
"""
The raw data begins with a header that contains information that is useful for transferring the waveform.
We will need to read it and then remove it from the actual waveform data.
The first character in the header is a '#' character.
The second character contains the number of digits in the number of data points in the record
(for example if the number of data points was 100, this character would be 3).
The next number is the number of data points whose length is specified by the second character
A full example: If I had a 1000 point-long waveform, the header would be '#41000'
"""
#determine the length of the header by adding 2 to the number of digits in the waveform length
headerlength = 2 + int(rawdata[1])
#save the header if you like
header = rawdata[:headerlength]
#strip out the header by saving the data from the end of the header to the index before end of the waveform
#the last data point is excluded because it is a newline character
rawdata = rawdata[headerlength:-1]
print('Curve query received.')

"""
This one is a bit tricky if you've never used unpack() before, so this is what it does:
Create an array using the numpy module, and unpack this array (convert it from a string)
The syntax of unpack is a string that contains the length of the string to be converted directly followed
by a character that represents the data type to which you'd like to convert and then the target string.
So in other words, this is the syntax: unpack('<length><DataType>',targetString).
The length of the data is specified by numberofpoints and inserted to the string using the 'string'.format() method
"""
data = numpy.array(unpack('{0}b'.format(numberofpoints), rawdata))


"""#################PLOTS#################"""
"""
Using the scaling information, rescale the binary data
Subtract the vertical offset (modified by the vertical offset) from the binary data, multiply the resulting
data by the ymultiplier, and then add the yzero (modified by the vertical position)
order of operations is important because yoffset is raw, unscaled binary
data and yzero has been scaled
"""
scaleddata = (data-yoffset)*ymult+yzero

#Create a time vector starting at xzero, ending at the end of the record,
#with the same number of points as the record length
scaledtime = np.arange(xzero,xzero+(xincrement*numberofpoints),xincrement)

print('Plot generated.')
#plot the figure with correct scaling
plt.subplot(111, axisbg='k')
plt.plot(scaledtime*1e3,scaleddata,'y')
plt.ylabel('Voltage (V)')
plt.xlabel('Time (msec)')
plt.show()
