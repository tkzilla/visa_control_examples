"""
VISA Control: RSA AvT Transfer
Author: Morgan Allison
Updated: 11/17
This program transfers the Amplitude vs Time trace from the RSA to the
computer and plots the results.
Windows 7 64-bit, TekVISA 4.0.4, Python 3.6.3 64-bit
NumPy 1.13.3, MatPlotLib 2.1.0, PyVISA 1.8
To get PyVISA: pip install pyvisa
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy and MatPlotLib
Download SignalVu-PC programmer manual:
https://www.tek.com/product-software-series/signalvu-pc-manual/signalvu-pc-1
Download RSA5100B programmer manual:
http://www.tek.com/spectrum-analyzer/inst5000-manual-7
Tested on RSA306B, RSA507A, and RSA5126B
"""

import visa
import numpy as np
import matplotlib.pyplot as plt

"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
rsa = rm.open_resource('GPIB8::1::INSTR')
rsa.timeout = 10000
rsa.encoding = 'latin_1'
rsa.write_termination = None
rsa.read_termination = '\n'
print(rsa.query('*idn?'))
rsa.write('*rst')
rsa.write('*cls')

"""#################CONFIGURE INSTRUMENT#################"""
# Configuration parameters.
cf = 2.4453e9
span = 40e6
refLevel = 0
timeScale = 100e-6
timeOffset = -10e-6
trigLevel = -10

# Stop acquisitions while setting up instrument.
rsa.write('abort')

# Open spectrum, time overview, and amplitude vs time displays.
rsa.write('display:general:measview:new spectrum')
rsa.write('display:general:measview:new toverview')
rsa.write('display:general:measview:new avtime')

# Configure amplitude vs time measurement.
rsa.write('spectrum:frequency:center {}'.format(cf))
rsa.write('spectrum:frequency:span {}'.format(span))
rsa.write('input:rlevel {}'.format(refLevel))
rsa.write('sense:avtime:span {}'.format(span))
rsa.write('sense:analysis:length {}'.format(timeScale))
rsa.write('sense:analysis:start {}'.format(timeOffset))

# Configure power level trigger.
rsa.write('trigger:event:input:type power')
rsa.write('trigger:event:input:level {}'.format(trigLevel))

# Configure acquisition mode
rsa.write('initiate:continuous off')
rsa.write('trigger:status on')

"""#################ACQUIRE DATA#################"""
# Start acquisition.
rsa.write('initiate:immediate')
rsa.query('*opc?')

# Get raw amplitude vs time data from RSA.
avt = rsa.query_binary_values('fetch:avtime:first?', datatype='f', container=np.array)

"""#################PLOT DATA#################"""
# Create time vector for plotting.
acqStart = float(rsa.query('display:avtime:x:scale:offset?'))
acqEnd = float(rsa.query('display:avtime:x:scale:full?'))
time = np.linspace(acqStart, acqEnd, len(avt))

# plot the data
fig = plt.figure(1, figsize=(10, 7))
ax = fig.add_subplot(111, facecolor='k')
ax.plot(time, avt, 'y')
ax.set_title('Amplitude vs Time')
ax.set_ylabel('Amplitude (dBm)')
ax.set_xlabel('Time (s)')
ax.set_xlim(acqStart, acqEnd)
plt.show()

rsa.close()
