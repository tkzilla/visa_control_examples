"""
VISA: RSA Digital Demod
Author: Morgan Allison
Date created: 1/17
Date edited: 2/17
This program sets up RSA5k/SignalVu-PC/SignalVu remotely to
acquire and demodulate a 1 MHz QPSK signal with RRC filter 
and alpha of 0.3.
Windows 7 64-bit
Python 3.6.0 64-bit (Anaconda 4.3.0)
NumPy 1.11.2, MatPlotLib 2.0.0
Download Anaconda: http://continuum.io/downloads
Download SignalVu-PC programmer manual: http://www.tek.com/node/1828803
Download RSA5100B programmer manual: 
http://www.tek.com/spectrum-analyzer/inst5000-manual-7
Tested on RSA306B, RSA5126B and MSO73304DX with SignalVu
"""

import visa
import numpy as np
import matplotlib.pyplot as plt

"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
inst = rm.open_resource('TCPIP::127.0.0.1::INSTR')	
inst.timeout = 25000
instId = inst.ask('*idn?')
print(instId)
if 'MSO' in instId or 'DPO' in instId:
	# IMPORTANT: make sure SignalVu is already running if you're using a scope.
	# The application:activate command gives focus to SignalVu.
	# *OPC? does not respond to application:activate, so there's no good 
	# way to synchronize this command
	print('Configuring SignalVu on instrument.')
	inst.write('application:activate \"SignalVu Vector Signal Analysis Software\"')

# preset, clear buffer, and stop acquisition
inst.write('system:preset')
inst.write('*cls')
inst.write('abort')
 

"""#################CONFIGURE INSTRUMENT#################"""
freq = 1e9
span = 5e6
refLevel = 0

# set up spectrum acquisition parameters
inst.write('spectrum:frequency:center {}'.format(freq))
inst.write('spectrum:frequency:span {}'.format(span))
inst.write('input:rlevel {}'.format(refLevel))

# open new displays
inst.write('display:ddemod:measview:new conste') # constellation
inst.write('display:ddemod:measview:new stable') # symbol table
inst.write('display:ddemod:measview:new evm') # EVM vs Time

# turn off trigger and disable continuous capture (enable single shot mode)
inst.write('trigger:status off')
inst.write('initiate:continuous off')

# configure digital demodulation (QPSK, 1 MSym/s, RRC/RC filters, alpha 0.3)
symRate = 1e6
alpha = 0.3

inst.write('sense:ddemod:modulation:type qpsk')
inst.write('sense:ddemod:srate {}'.format(symRate))
inst.write('sense:ddemod:filter:measurement rrcosine')
inst.write('sense:ddemod:filter:reference rcosine')
inst.write('sense:ddemod:filter:alpha {}'.format(alpha))

# start acquisition
inst.write('initiate:immediate')
# wait for acquisition to finish
inst.ask('*opc?')

# query results from the constellation display (details in programmer manual)
results = inst.ask('fetch:conste:results?')

# remove terminating whitespace (.rstrip()), split the string result (.split())
# into an array of 3 values, and convert those values to floating point numbers
results = results.rstrip().split(',')
evm = [float(value) for value in results]

# print out the results
# see Python's format spec docs for more details: https://goo.gl/YmjGzV
print('EVM (RMS): {0[0]:2.3f}%, EVM (peak): {0[1]:2.3f}%, Symbol: {0[2]:<4.0f}'
	.format(evm))

# get EVM vs time data
evmVsTime = inst.query_binary_values('fetch:evm:trace?')

# determine points per symbol to create a plottable x axis
ptsPerSymbol = inst.ask('sense:ddemod:symbol:points?')
if ptsPerSymbol == 'ONE\n':
    ptsPerSymbol = 1.0
elif ptsPerSymbol == 'TWO\n':
    ptsPerSymbol = 2.0
elif ptsPerSymbol == 'FOUR\n':
    ptsPerSymbol = 4.0
elif ptsPerSymbol == 'EIGHT\n':
    ptsPerSymbol = 8.0
else:
    ptsPerSymbol = 4.0    # default

symbol = np.array(range(len(evmVsTime)))/ptsPerSymbol

plt.plot(symbol, evmVsTime)
plt.title('EVM vs Symbol #')
plt.xlabel('Symbol')
plt.ylabel('EVM (%)')
plt.show()

inst.close()
