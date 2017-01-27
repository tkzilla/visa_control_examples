"""
VISA: RSA Spectrum Trace Transfer
Author: Morgan Allison
Date created: Unknown
Date edited: 1/17
This program transfers the Spectrum trace from the RSA to the 
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
rsa.write('abort')


"""#################CONFIGURE INSTRUMENT#################"""
#configure acquisition parameters
cf = 1e9
span = 40e6
refLevel = 0
rsa.write('spectrum:frequency:center {}'.format(cf))
rsa.write('spectrum:frequency:span {}'.format(span))
rsa.write('input:rlevel {}'.format(refLevel))

rsa.write('initiate:continuous off')
rsa.write('trigger:status off')


"""#################ACQUIRE/PROCESS DATA#################"""
#start acquisition THIS MUST BE DONE
#it is an overlapping command, so *OPC? MUST be sent for synchronization
rsa.write('initiate:immediate')
rsa.ask('*opc?')

spectrum = rsa.query_binary_values('fetch:spectrum:trace?', datatype='f', 
	container=np.array)

#generate the frequency vector for plotting
fMin = cf-span/2
fMax = cf+span/2
freq = np.linspace(fMin, fMax, len(spectrum))


"""#################PLOTS#################"""
fig = plt.figure(1, figsize=(20,10))
ax = fig.add_subplot(111, axisbg='k')
ax.plot(freq/1e9, spectrum, 'y')
ax.set_title('Spectrum')
ax.set_xlabel('Frequency (GHz)')
ax.set_ylabel('Amplitude (dBm)')
ax.set_xlim(fMin/1e9, fMax/1e9)
ax.set_ylim(refLevel-100, refLevel)
plt.show()

rsa.close()
