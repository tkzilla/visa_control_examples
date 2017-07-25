"""
VISA Control: DPO Delay/Position Example
Author: Morgan Allison
Date Created: 9/2014
Date Edited: 5/2017
This script configures horizontal delay and position, grabs the waveform
data, and adjusts the queried data so that the plot returns the correct
time values for the acquisition.
Windows 7 64-bit, TekVISA 4.0.4
Python 3.6.0 64-bit (Anaconda 4.3.0)
NumPy 1.11.2, MatPlotLib 2.0.0, PyVISA 1.8
To get PyVISA: pip install pyvisa
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy and MatPlotLib
Download SignalVu-PC programmer manual: http://www.tek.com/node/1828803
Tested on DPO77002SX
####################
SignalVu must be running on the scope for this script to work correctly
####################
"""

import visa
import numpy as np
import matplotlib.pyplot as plt


def get_waveform_info():
    dpo.write('acquire:stopafter sequence')
    dpo.write('acquire:state on')
    dpo.ask('*OPC?')
    binaryFormat = dpo.ask('wfmoutpre:bn_fmt?').rstrip()
    print('Binary format: ', binaryFormat)
    numBytes = dpo.ask('wfmoutpre:byt_nr?').rstrip()
    print('Number of Bytes: ', numBytes)
    byteOrder = dpo.ask('wfmoutpre:byt_or?').rstrip()
    print('Byte order: ', byteOrder)
    encoding = dpo.ask('data:encdg?').rstrip()
    print('Encoding: ', encoding)
    if 'RIB' in encoding or 'FAS' in encoding:
        dType = 'b'
        bigEndian = True
    elif encoding.startswith('RPB'):
        dType = 'B'
        bigEndian = True
    elif encoding.startswith('SRI'):
        dType = 'b'
        bigEndian = False
    elif encoding.startswith('SRP'):
        dType = 'B'
        bigEndian = False
    elif encoding.startswith('FP'):
        dType = 'f'
        bigEndian = True
    elif encoding.startswith('SFP'):
        dType = 'f'
        bigEndian = False
    elif encoding.startswith('ASCI'):
        raise visa.InvalidBinaryFormat('ASCII Formatting.')
    else:
        raise visa.InvalidBinaryFormat
    return dType, bigEndian

"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
dpo = rm.open_resource('TCPIP::192.168.1.14::INSTR')
dpo.encoding = 'latin_1'
dpo.write_termination = None
dpo.read_termination = '\n'
dpo.write('*rst')
print('Connected to: ', dpo.ask('*IDN?'))

dpo.write('horizontal:mode:scale 20e-9')
# dpo.write('select:ch3 on')
# dpo.write('ch3:scale 400e-3')
# dpo.write('trigger:a:edge:source aux')
# dpo.write('trigger:a:level 400e-3')

dpo.write('horizontal:delay:mode 1')
dMode = dpo.ask('horizontal:delay:mode?').strip()
print('Delay mode: ', dMode)

dPos = 30
dpo.write('horizontal:delay:position {}'.format(dPos))
dPos = dpo.ask('horizontal:delay:position?').strip()
print('Delay position: ', dPos)

dTime = 250e-9
dpo.write('horizontal:delay:time {}'.format(dTime))
dTime = float(dpo.ask('horizontal:delay:time?').strip())
print('Delay time: ', dTime)

ptOffset = int(dpo.ask('wfmoutpre:pt_off?').strip())
print('Point offset: ', ptOffset)

recordLength = int(dpo.ask('horizontal:mode:recordlength?').strip())
print('Record Length: ', recordLength)

dpo.write('acquire:stopafter sequence')
dpo.write('acquire:state on')

dpo.write('data:source ch1')
dpo.write('data:stop {}'.format(recordLength))
numPoints = int(dpo.ask('wfmoutpre:nr_pt?'))

# amount of time between data points
xIncr = float(dpo.ask('wfmoutpre:xincr?'))
# absolute time value of the beginning of the waveform record
xZero = float(dpo.ask('wfmoutpre:xZero?'))
print('xZero: {}, xIncr: {}'.format(xZero, xIncr))

start = -dTime + (xIncr * -ptOffset)
stop = -dTime + xIncr * (numPoints - ptOffset)
scaledTime = np.linspace(start, stop, numPoints)

dType, bigEndian = get_waveform_info()
dpo.write('header on')
print(dpo.ask('wfmoutpre?'))
dpo.write('header off')

data = dpo.query_binary_values('curve?', datatype=dType, is_big_endian=bigEndian, container=np.array)
plt.plot(scaledTime, data)
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.axvline(0, color='y')
plt.show()

dpo.close()
