"""
AWG70k Simple Waveform Sender
Creates a simple sine wave, sends it to the AWG, assigns
it to Ch1 and plays it out.
Edited: 9/17
Windows 7 64-bit
Python 3.6.0 64-bit (Anaconda 4.3.0)
NumPy 1.13.1, PyVISA 1.8
Get Anaconda: http://continuum.io/downloads
Anaconda includes NumPy
Get PyVISA: pip install pyvisa
"""

import visa
import numpy as np
print('NumPy Version:', np.__version__)
print('PyVISA Version:', visa.__version__)

# Set up VISA instrument object
rm = visa.ResourceManager()
awg = rm.open_resource('GPIB8::1::INSTR')
awg.timeout = 25000
awg.encoding = 'latin_1'
awg.write_termination = None
awg.read_termination = '\n'
print('Connected to ', awg.query('*idn?'))
awg.write('*rst')
awg.write('*cls')


# Change these based on your signal requirements
name = 'test_wfm'
sampleRate = 10e9
recordLength = 500000
freq = 100e6

# Create Waveform
t = np.linspace(0, recordLength/sampleRate, recordLength, dtype=np.float32)
wfmData = np.sin(2*np.pi*freq*t)

# Create Marker Data
# Marker data is an 8 bit value. Bit 6 is marker 1 and bit 7 is marker 2
exData1 = (1 << 6) * np.random.randint(2, size=recordLength, dtype=np.uint8)
exData2 = (1 << 7) * np.random.randint(2, size=recordLength, dtype=np.uint8)

markerData = exData1 + exData2

# Send Waveform Data
awg.write('wlist:waveform:new "{}", {}'.format(name, recordLength))
stringArg = 'wlist:waveform:data "{}", 0, {}, '.format(name, recordLength)
awg.write_binary_values(stringArg, wfmData)
awg.query('*opc?')

# Send Marker Data
stringArg = 'wlist:waveform:marker:data "{}", 0, {}, '.format(name, recordLength)
awg.write_binary_values(stringArg, markerData, datatype='B')
awg.query('*opc?')

# Load waveform, being playback, and turn on output
awg.write('source1:waveform "{}"'.format(name))
awg.write('awgcontrol:run:immediate')
awg.query('*opc?')
awg.write('output1 on')


# Check for errors
error = awg.query('system:error:all?')
print('Status: {}'.format(error))

awg.close()
