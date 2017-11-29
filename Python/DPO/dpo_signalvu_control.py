"""
VISA Control: AvT and Spectrum Trace Transfer from SignalVu
Author: Morgan Allison
Updated: 11/17
Transfers the Spectrum and Amplitude vs Time traces from the scope
to the computer and plots the results. Test signal was a 10 us
10% duty cycle CW pulse centered at 2.4453 GHz.
Windows 7 64-bit, TekVISA 4.0.4
Python 3.6.3 64-bit (Anaconda 4.4.0)
NumPy 1.13.3, MatPlotLib 2.0.2, PyVISA 1.8
To get PyVISA: pip install pyvisa
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy and MatPlotLib
Download SignalVu-PC programmer manual:
https://www.tek.com/oscilloscope/dpo70000-mso70000-manual-22
Tested on DPO77002SX
####################
SignalVu must be running on the scope for this script to work correctly
####################
"""

import visa
import numpy as np
import matplotlib.pyplot as plt

"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
dpo = rm.open_resource('TCPIP::192.168.1.4::INSTR')
dpo.timeout = 10000
dpo.encoding = 'latin_1'
dpo.write_termination = None
dpo.read_termination = '\n'
print(dpo.query('*idn?'))
dpo.write('*rst')
dpo.query('*opc?')
dpo.query('system:error:all?')


"""#################CONFIGURE INSTRUMENT#################"""
# configure acquisition parameters
cf = 2.4453e9
span = 100e6
analysisLength = 20e-6
analysisOffset = 1e-6
spectrumOffset = 5e-6

print('Configuring SignalVu-PC on instrument.')
dpo.write('application:activate \"SignalVu Vector Signal Analysis Software\"')
dpo.query('*opc?')

# reset the instrument
dpo.write('system:preset')
dpo.query('*opc?')
dpo.write('display:general:measview:new toverview')
dpo.write('display:general:measview:new avtime')

# configure amplitude vs time measurement
dpo.write('spectrum:frequency:center {}'.format(cf))
dpo.write('spectrum:frequency:span {}'.format(span))
dpo.write('sense:avtime:span {}'.format(span))
dpo.write('sense:acquisition:seconds {}'.format(analysisLength))
dpo.write('sense:analysis:reference acqstart')
dpo.write('sense:analysis:length {}'.format(analysisLength))
dpo.write('sense:analysis:start {}'.format(analysisOffset))
dpo.write('sense:spectrum:start {}'.format(spectrumOffset))


"""#################ACQUIRE DATA#################"""
# start acquisition
dpo.write('initiate:continuous off')
dpo.write('initiate:immediate')
dpo.query('*opc?')

# get amplitude vs time data
print('Getting AvT trace.')
avt = dpo.query_binary_values('fetch:avtime:first?')
dpo.query('*opc?')

# get the minimum and maximum time in the measurement from the scope
timeMax = float(dpo.query('display:avtime:x:scale:full?'))
timeMin = float(dpo.query('display:avtime:x:scale:offset?'))

# get spectrum trace from signalvu
print('Getting spectrum trace.')
spectrum = dpo.query_binary_values('fetch:spectrum:trace1?')
dpo.query('*opc?')


"""#################PLOT DATA#################"""
# generate the time vector for plotting
increment = (timeMax - timeMin) / len(avt)
time = np.arange(timeMin, timeMax - increment, increment)

# generate the frequency vector for plotting
fMin = cf - (span / 2)
fMax = cf + (span / 2)
increment = (fMax - fMin) / len(spectrum)
freq = np.arange(fMin, fMax, increment)
# print('Spectrum length: {}'.format(len(spectrum)))
# print('Freq length: {}'.format(len(freq)))

print('Plotting data.')
fig = plt.figure(1, figsize=(15, 10))
ax1 = fig.add_subplot(211, facecolor='k')
ax1.set_title('Spectrum Trace', loc='left')
ax1.set_ylabel('Amplitude (dBm)')
ax1.set_xlabel('Frequency (Hz)')
ax1.plot(freq, spectrum, 'y')
ax1.set_xlim(fMin, fMax)

ax2 = fig.add_subplot(212, facecolor='k')
ax2.set_title('Amplitude vs Time', loc='left')
ax2.set_ylabel('Amplitude (dBm)')
ax2.set_xlabel('Time (s)')
ax2.plot(time, avt, 'y')
ax2.set_xlim(timeMin, timeMax)

plt.tight_layout()
plt.show()

dpo.close()
