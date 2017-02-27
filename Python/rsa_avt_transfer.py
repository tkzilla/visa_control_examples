"""
VISA Control: RSA AvT Transfer
Author: Morgan Allison
Date Created: 9/14
Date Edited: 1/17
This program transfers the Amplitude vs Time trace from the RSA to the 
computer and plots the results. 
Windows 7 64-bit, TekVISA 4.0.4
Python 3.5.2 64-bit (Anaconda 4.2.0)
NumPy 1.11.2, MatPlotLib 1.5.3, PyVISA 1.5
To get Anaconda: http://continuum.io/downloads
Tested on RSA306B and RSA5126B
"""

import visa
import numpy as np
import matplotlib.pyplot as plt


"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
rsa = rm.open_resource('GPIB8::1::INSTR')
rsa.timeout = 10000
print(rsa.ask('*idn?'))
rsa.write('*rst')
rsa.write('*cls')


"""#################INITIALIZE VARIABLES#################"""
# configure acquisition parameters
cf = 2.4453e9
span = 40e6
refLevel = -40
timeScale = 100e-6
timeOffset = 0
trigLevel = -50


"""#################CONFIGURE INSTRUMENT#################"""
# stop acquisitions while setting up instrument
rsa.write('abort')

# open spectrum, time overview, and amplitude vs time displays
rsa.write('display:general:measview:new spectrum')
rsa.write('display:general:measview:new toverview')
rsa.write('display:general:measview:new avtime')

# configure amplitude vs time measurement
rsa.write('spectrum:frequency:center {}'.format(cf))
rsa.write('spectrum:frequency:span {}'.format(span))
rsa.write('input:rlevel {}'.format(refLevel))
rsa.write('sense:avtime:span {}'.format(span))
rsa.write('sense:analysis:length {}'.format(timeScale))
rsa.write('sense:analysis:start {}'.format(timeOffset))

# configure power level trigger
rsa.write('trigger:event:input:type power')
rsa.write('trigger:event:input:level {}'.format(trigLevel))
rsa.write('initiate:continuous off')
rsa.write('trigger:status on')


"""#################ACQUIRE/PROCESS DATA#################"""
# start acquisition
rsa.write('initiate:immediate')
rsa.ask('*opc?')

# get raw amplitude vs time data from RSA
avt = rsa.query_binary_values('fetch:avtime:first?', datatype='f',
	container=np.array)

acqStart = float(rsa.ask('display:avtime:x:scale:offset?'))
acqEnd = float(rsa.ask('display:avtime:x:scale:full?'))
time = np.linspace(acqStart,acqEnd, len(avt))


"""#################PLOTS#################"""
# plot the data
fig = plt.figure(1, figsize=(20,10))
ax = fig.add_subplot(111, axisbg='k')
ax.plot(time, avt, 'y')
ax.set_title('Amplitude vs Time')
ax.set_ylabel('Amplitude (dBm)')
ax.set_xlabel('Time (s)')
ax.set_xlim(acqStart,acqEnd)
plt.show()