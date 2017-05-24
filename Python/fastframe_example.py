"""
VISA Control: FastFrame Summary Frame Transfer
Author: Morgan Allison
Date Created: 6/2014
Date Edited: 5/2017
This program acquires 10 instances of a pulse train that contains a 
periodic runt using FastFrame and transfers the summary frame to the computer.
Windows 7 64-bit, TekVISA 4.0.4
Python 3.6.0 64-bit (Anaconda 4.3.0)
NumPy 1.11.2, MatPlotLib 2.0.0, PyVISA 1.8
To get PyVISA: pip install pyvisa
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy and MatPlotLib
Download SignalVu-PC programmer manual: http://www.tek.com/node/1828803
Tested on Tested on DPO5204B, MSO72004, and DPO7104C
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
# establish communication with dpo
rm = visa.ResourceManager()
dpo = rm.open_resource('TCPIP::192.168.1.14::INSTR')
dpo.timeout = 10000
dpo.encoding = 'latin_1'
dpo.write_termination = None
dpo.read_termination = '\n'
print(dpo.query('*idn?'))
dpo.write('*rst')
dpo.query('system:error:all?')


"""#################INITIALIZE VARIABLES#################"""
# variables for individual settings
hScale = 200e-9
sRate = 2.5e9
numFrames = 10
vScale = .2
vPos = 0
hiThresh = 0.4
lowThresh = 0.2


"""#################CONFIGURE INSTRUMENT#################"""
# dpo setup
dpo.write('acquire:state off')
dpo.write('horizontal:mode auto')
dpo.write('horizontal:mode:scale {}'.format(hScale))
dpo.write('horizontal:mode:samplerate {}'.format(sRate))
dpo.write('acquire:mode sample')
dpo.write('horizontal:fastframe:state on')
dpo.write('horizontal:fastframe:count {}'.format(numFrames))
dpo.write('ch1:scale {}'.format(vScale))
dpo.write('ch1:position {}'.format(vPos))
dpo.write('trigger:a:type pulse')
dpo.write('trigger:a:pulse:class runt')
dpo.write('trigger:a:pulse:runt:qualify occurs')
dpo.write('trigger:a:pulse:runt:polarity:ch1 positive')
dpo.write('trigger:a:pulse:runt:threshold:high {}'.format(hiThresh))
dpo.write('trigger:a:pulse:runt:threshold:low {}'.format(lowThresh))
print('Horizontal, vertical, and trigger settings configured.')

# configure data transfer settings
dpo.write('header off')
dpo.write('horizontal:fastframe:sumframe average')
dpo.write('data:encdg fastest')
dpo.write('data:source ch1')
recordLength = int(dpo.query('horizontal:mode:recordlength?').strip())
dpo.write('data:stop {}'.format(recordLength))
dpo.write('wfmoutpre:byt_n 1')
dpo.write('data:framestart 10')
dpo.write('data:framestop 10')
print('Data transfer settings configured.')


"""#################ACQUIRE/PROCESS DATA#################"""
print('Acquiring waveform.')
# dpo.Timeout = 60
dpo.write('acquire:stopafter sequence')
dpo.write('acquire:state on')
dpo.query('*opc?')
print('Waveform acquired.\n')

# Retrieve vertical and horizontal scaling information
yOffset = float(dpo.query('wfmoutpre:yoff?'))
yMult = float(dpo.query('wfmoutpre:ymult?'))
yZero = float(dpo.query('wfmoutpre:yzero?'))

numPoints = int(dpo.query('wfmoutpre:nr_pt?'))
xIncr = float(dpo.query('wfmoutpre:xincr?'))
xZero = float(dpo.query('wfmoutpre:xzero?'))

dType, bigEndian = get_waveform_info()
data = dpo.query_binary_values(
    'curve?', datatype=dType, is_big_endian=bigEndian, container=np.array)

"""#################PLOTS#################"""
# Using the scaling information, rescale the binary data
scaleddata = (data-yOffset)*yMult+yZero
scaledtime = np.arange(xZero, xZero+(xIncr*numPoints), xIncr)

print('Plot generated.')
# plot the figure with correct scaling
plt.subplot(111, facecolor='k')
plt.plot(scaledtime*1e3, scaleddata, color='y')
plt.ylabel('Voltage (V)')
plt.xlabel('Time (msec)')
plt.show()

dpo.close()
