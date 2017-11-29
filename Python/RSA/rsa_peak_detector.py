"""
VISA: Peak Detector
Author: Morgan Allison
Updated: 11/17
This program tracks the peak frequency 10 times, writes the results
to a csv file, and creates a scatter plot of the results.
Windows 7 64-bit, TekVISA 4.0.4, Python 3.6.3 64-bit
PyVISA 1.8, Matplotlib 2.1.0
To get PyVISA: pip install pyvisa
To get Anaconda: http://continuum.io/downloads
Anaconda includes Matplotlib
Download SignalVu-PC programmer manual:
https://www.tek.com/product-software-series/signalvu-pc-manual/signalvu-pc-1
Download RSA5100B programmer manual:
http://www.tek.com/spectrum-analyzer/inst5000-manual-7
Tested on RSA306B, RSA507A, RSA5126B
"""

import visa
from csv import writer
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
freq = 2e9
span = 40e6
rbw = 100
refLevel = 0

# Configure spectrum capture
rsa.write('spectrum:frequency:center {}'.format(freq))
rsa.write('spectrum:frequency:span {}'.format(span))
rsa.write('spectrum:bandwidth {}'.format(rbw))
rsa.write('input:rlevel {}'.format(refLevel))

actualFreq = float(rsa.query('spectrum:frequency:center?'))
actualSpan = float(rsa.query('spectrum:frequency:span?'))
actualRbw = float(rsa.query('spectrum:bandwidth?'))
actualRefLevel = float(rsa.query('input:rlevel?'))

# Sanity check.
print('CF: {} Hz'.format(actualFreq))
print('Span: {} Hz'.format(actualSpan))
print('RBW: {} Hz'.format(actualRbw))
print('Reference Level: {}\n'.format(actualRefLevel))

rsa.write('trigger:status off')
rsa.write('initiate:continuous off')

"""#################ACQUIRE DATA#################"""
# Add marker for measurement
rsa.write('calculate:marker:add')
peakFreq = []
peakAmp = []
n = 10
with open('peak_detector.csv', 'w') as f:
    w = writer(f, lineterminator='\n')
    w.writerow(['Frequency', 'Amplitude'])
    # Acquisition/measurement loop.
    for i in range(n):
        rsa.write('initiate:immediate')
        rsa.query('*opc?')

        rsa.write('calculate:spectrum:marker0:maximum')
        peakFreq.append(float(rsa.query('calculate:spectrum:marker0:X?')))
        peakAmp.append(float(rsa.query('calculate:spectrum:marker0:Y?')))
        w.writerow([peakFreq[i], peakAmp[i]])

plt.scatter(peakFreq, peakAmp)
plt.title('Scatter Plot of Amplitude vs Frequency')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude (dBm)')
plt.xlim((freq - span / 2), (freq + span / 2))
plt.ylim(refLevel, refLevel - 100)
plt.tight_layout()
plt.show()

rsa.close()
