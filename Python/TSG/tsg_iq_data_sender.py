"""
TSG Data Sender
Author: Morgan Allison
Updated: 03/18
This script allows you to send IQ data to
the TSG and utulize its internal baseband generator
to use it as a simple IQ modulator.
This example creates a 10 kHz dual sideband modulation.
Windows 10 64-bit, 4.2.15 (AWG only)
Python 3.6.4 64-bit
PyVISA 1.8, NumPy 1.13.1
"""

import visa
import numpy as np

rm = visa.ResourceManager()
tsg = rm.open_resource('TCPIP0::192.168.1.12::INSTR')

tsg.write('*RST')
instID = tsg.query('*idn?')
print('Connected to {}'.format(instID))

# Create waveform data
# Simple sine wave for I, zero vector for Q.
# NOTE: max sample rate is 6 MHz
sampleRate = 6e6
recordLength = 600
freq = 10e3

# Create Waveform
t = np.linspace(0, recordLength / sampleRate, recordLength)
# Scale the amplitude for int16 values
i = np.array(32767 * np.sin(2 * np.pi * freq * t), dtype=np.int16)
q = np.zeros(recordLength, dtype=np.int16)

# Create interleaved IQ waveform
iq = np.empty((i.size + q.size), dtype=i.dtype)
iq[0::2] = i
iq[1::2] = q

# Send IQ data to TSG into SRAM (waveform location 0)
# Send data as big endian and ensure your data type is 'h' for int16
tsg.write_binary_values('wrtw 2, {}, '.format(len(iq) * 16), iq, datatype='h', is_big_endian=True)

# Configure amplitude and frequency
tsg.write('ampr 0')
tsg.write('freq 1 GHz')

# Select phase modulation
tsg.write('type 2')
# Vector modulation subtype
tsg.write('styp 1')
# User waveform source
tsg.write('qfnc 11')
# Load waveform sent previously
tsg.write('wavf 0')
# Configure sample rate
tsg.write('symr {}'.format(sampleRate))

# Turn on modulation and RF output
tsg.write('modl 1')
tsg.write('enbr 1')

tsg.close()
