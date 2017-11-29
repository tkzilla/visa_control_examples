"""
VISA Control: DPO Delay/Position Example
Author: Morgan Allison
Updated: 11/17
Configures horizontal delay and position, grabs the waveform
data, and adjusts the queried data so that the plot returns
the correct time values for the acquisition.
Windows 7 64-bit, TekVISA 4.0.4
Python 3.6.3 64-bit (Anaconda 4.4.0)
NumPy 1.13.3, MatPlotLib 2.0.2, PyVISA 1.8
To get PyVISA: pip install pyvisa
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy and MatPlotLib
Tested on DPO77002SX, MSO58
"""

import visa
import numpy as np
import matplotlib.pyplot as plt


def get_waveform_info():
    dpo.write('acquire:stopafter sequence')
    dpo.write('acquire:state on')
    dpo.query('*OPC?')
    binaryFormat = dpo.query('wfmoutpre:bn_fmt?').rstrip()
    print('Binary format: ', binaryFormat)
    numBytes = dpo.query('wfmoutpre:byt_nr?').rstrip()
    print('Number of Bytes: ', numBytes)
    byteOrder = dpo.query('wfmoutpre:byt_or?').rstrip()
    print('Byte order: ', byteOrder)
    encoding = dpo.query('data:encdg?').rstrip()
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
dpo = rm.open_resource('TCPIP::192.168.1.8::INSTR')
dpo.encoding = 'latin_1'
dpo.write_termination = None
dpo.read_termination = '\n'
dpo.write('*rst')
print('Connected to: ', dpo.query('*IDN?'))

"""#################CONFIGURE INSTRUMENT#################"""
hScale = 20e-9
dPos = 30
dTime = 250e-9

dpo.write('horizontal:mode:scale {}'.format(hScale))

dpo.write('horizontal:delay:mode on')
dMode = dpo.query('horizontal:delay:mode?').strip()
print('Delay mode: ', dMode)

dpo.write('horizontal:delay:position {}'.format(dPos))
dPos = dpo.query('horizontal:delay:position?').strip()
print('Delay position: ', dPos)

dpo.write('horizontal:delay:time {}'.format(dTime))
dTime = float(dpo.query('horizontal:delay:time?').strip())
print('Delay time: ', dTime)

ptOffset = int(dpo.query('wfmoutpre:pt_off?').strip())
print('Point offset: ', ptOffset)

recordLength = int(dpo.query('horizontal:mode:recordlength?').strip())
print('Record Length: ', recordLength)

dpo.write('data:source ch1')
dpo.write('data:stop {}'.format(recordLength))
numPoints = int(dpo.query('wfmoutpre:nr_pt?'))

"""#################ACQUIRE DATA#################"""
dpo.write('acquire:stopafter sequence')
dpo.write('acquire:state on')

dType, bigEndian = get_waveform_info()
dpo.write('header on')
print(dpo.query('wfmoutpre?'))
dpo.write('header off')

data = dpo.query_binary_values('curve?', datatype=dType, is_big_endian=bigEndian, container=np.array)

"""#################PLOT DATA#################"""
# amount of time between data points
xIncr = float(dpo.query('wfmoutpre:xincr?'))
# absolute time value of the beginning of the waveform record
xZero = float(dpo.query('wfmoutpre:xZero?'))
print('xZero: {}, xIncr: {}'.format(xZero, xIncr))

# create correctly scaled time vector for plotting
start = -dTime + (xIncr * -ptOffset)
stop = -dTime + xIncr * (numPoints - ptOffset)
scaledTime = np.linspace(start, stop, numPoints)

plt.plot(scaledTime, data)
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')
plt.axvline(0, color='y')
plt.show()

dpo.close()
