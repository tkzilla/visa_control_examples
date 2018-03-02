"""
VISA Control: RSA IQ Transfer
Author: Morgan Allison
Updated: 03/18
This program transfers the IQ vs Time trace from the RSA to the
computer and plots the results.
Windows 10 64-bit, TekVISA 4.2.15, Python 3.6.3 64-bit
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
cf = 1e9
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
rsa.write('display:general:measview:new iqvtime')

# Configure amplitude vs time measurement.
rsa.write('spectrum:frequency:center {}'.format(cf))
rsa.write('spectrum:frequency:span {}'.format(span))
rsa.write('input:rlevel {}'.format(refLevel))
rsa.write('sense:iqvtime:span {}'.format(span))
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
iq = rsa.query_binary_values('fetch:rfin:iq? 1', datatype='f', container=np.array)
i = iq[0:-2:2]
q = iq[1:-1:2]

"""#################PLOT DATA#################"""
# Create time vector for plotting.
acqStart = float(rsa.query('display:iqvtime:x:scale:offset?'))
acqEnd = acqStart + float(rsa.query('display:iqvtime:x:scale?'))
time = np.linspace(acqStart, acqEnd, len(i))

# plot the data
fig = plt.figure(1, figsize=(10, 7))
ax = fig.add_subplot(111, facecolor='k')
ax.plot(time, i, 'y')
ax.plot(time, q, 'c')
ax.set_title('IQ vs Time')
ax.set_ylabel('Voltage (V)')
ax.set_xlabel('Time (s)')
plt.show()

rsa.close()
