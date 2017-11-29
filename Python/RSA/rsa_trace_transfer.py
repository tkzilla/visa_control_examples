"""
VISA: RSA Spectrum Trace Transfer
Author: Morgan Allison
Updated: 11/17
This program transfers the Spectrum trace from the RSA to the
computer and plots the results.
Windows 7 64-bit, TekVISA 4.0.4, Python 3.6.3 64-bit
Numpy 1.13.3, Matplotlib 2.1.0, PyVISA 1.8
To get PyVISA: pip install pyvisa
To get Anaconda: http://continuum.io/downloads
Anaconda includes NumPy and Matplotlib
Download SignalVu-PC programmer manual:
https://www.tek.com/product-software-series/signalvu-pc-manual/signalvu-pc-1
Download RSA5100B programmer manual:
http://www.tek.com/spectrum-analyzer/inst5000-manual-7
Tested on RSA306B, RSA507A, RSA5126B
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
print('Connected to', rsa.query('*idn?'))

rsa.write('*rst')
rsa.write('*cls')
rsa.write('abort')

"""#################CONFIGURE INSTRUMENT#################"""
# Configure acquisition parameters.
cf = 2.4453e9
span = 40e6
refLevel = 0

rsa.write('spectrum:frequency:center {}'.format(cf))
rsa.write('spectrum:frequency:span {}'.format(span))
rsa.write('input:rlevel {}'.format(refLevel))

rsa.write('initiate:continuous off')
rsa.write('trigger:status off')

"""#################ACQUIRE DATA#################"""
rsa.write('initiate:immediate')
rsa.query('*opc?')

spectrum = rsa.query_binary_values('fetch:spectrum:trace?', datatype='f',
                                   container=np.array)

"""#################PLOTS#################"""
# Generate the frequency vector for plotting.
fMin = cf - span / 2
fMax = cf + span / 2
freq = np.linspace(fMin, fMax, len(spectrum))

fig = plt.figure(1, figsize=(15, 8))
ax = fig.add_subplot(111, facecolor='k')
ax.plot(freq / 1e9, spectrum, 'y')
ax.set_title('Spectrum')
ax.set_xlabel('Frequency (GHz)')
ax.set_ylabel('Amplitude (dBm)')
ax.set_xlim(fMin / 1e9, fMax / 1e9)
ax.set_ylim(refLevel - 100, refLevel)
plt.tight_layout()
plt.show()

rsa.close()
