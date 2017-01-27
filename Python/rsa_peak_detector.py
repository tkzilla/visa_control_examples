"""
VISA: Peak Detector
Author: Morgan Allison
Date created: Unknown
Date edited: 1/17
This program tracks the peak frequency 10 times, writes the results
to a csv file, and creates a scatter plot of the results.
Windows 7 64-bit
RSA API version 3.9.0029
Python 3.5.2 64-bit (Anaconda 4.2.0)
NumPy 1.11.2, MatPlotLib 1.5.3
Download Anaconda: http://continuum.io/downloads
Anaconda includes MatPlotLib
"""

import visa
from csv import writer
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
# configure acquisition parameters
freq = 2e9
span = 40e6
rbw = 100
refLevel = -50

rsa.write('spectrum:frequency:center {}'.format(freq))
rsa.write('spectrum:frequency:span {}'.format(span))
rsa.write('spectrum:bandwidth {}'.format(rbw))
rsa.write('input:rlevel {}'.format(refLevel))

actualFreq = float(rsa.ask('spectrum:frequency:center?'))
actualSpan = float(rsa.ask('spectrum:frequency:span?'))
actualRbw = float(rsa.ask('spectrum:bandwidth?'))
actualRefLevel = float(rsa.ask('input:rlevel?'))

print('CF: {} Hz'.format(actualFreq))
print('Span: {} Hz'.format(actualSpan))
print('RBW: {} Hz'.format(actualRbw))
print('Reference Level: {}'.format(actualRefLevel))
print()	#just some whitespace

rsa.write('trigger:status off')
rsa.write('initiate:continuous off')


"""#################ACQUIRE/PROCESS DATA#################"""
rsa.write('calculate:marker:add')
peakFreq = []
peakAmp = []
with open('peak_detector.csv', 'w') as f:
	w = writer(f, lineterminator='\n')	# by default the csv module uses \r\n
	w.writerow(['Frequency', 'Amplitude'])	# header row
	# acquisition and measurement loop
	for i in range(10):
		rsa.write('initiate:immediate')
		rsa.ask('*opc?')

		rsa.write('calculate:spectrum:marker0:maximum')
		peakFreq.append(float(rsa.ask('calculate:spectrum:marker0:X?')))
		peakAmp.append(float(rsa.ask('calculate:spectrum:marker0:Y?')))
		w.writerow([peakFreq[i], peakAmp[i]])

plt.scatter(peakFreq, peakAmp)
plt.title('Scatter Plot of Amplitude vs Frequency')
plt.xlabel('Frequency (Hz)')
plt.ylabel('Amplitude (dBm)')
plt.xlim((freq-span/2),(freq+span/2))
plt.ylim(refLevel, refLevel - 100)
plt.show()

rsa.close()
