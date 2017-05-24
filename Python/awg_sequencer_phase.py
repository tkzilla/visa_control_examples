"""
VISA: SourceXpress/AWG Sequence Builder and Channel Skew Adjuster
Author: Morgan Allison
Date created: 5/17
Date edited: 5/17
Creates a sequence of two waveforms with an external trigger dependency
and configures the AWG to change its phase between waveform outputs
Windows 7 64-bit
Python 3.6.0 64-bit (Anaconda 4.3.0)
NumPy 1.11.2, PyVISA 1.8, PyVISA-py 0.2
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy
"""

import visa
import numpy as np

# Change this to connect to your AWG as needed
"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager('@py')
awg = rm.open_resource('TCPIP::192.168.1.12::INSTR')
awg.timeout = 25000
print(awg.query('*idn?'))
awg.write('*rst')
awg.write('*cls')

recordLength = 50000
sampleRate = 5e9

name1 = 'deadTime'
deadTimeData = np.zeros(recordLength)

name2 = 'pulse'
pulseData = np.empty(recordLength)
pulseData[:int(recordLength/2)] = 1
pulseData[int(recordLength/2):] = -1

awg.write('wlist:waveform:del all')

seqName = 'Simple Sequence'
awg.write('slist:seq:delete "{}"'.format(seqName))
awg.write('slist:seq:new "{}", 2, 2'.format(seqName))   #2 steps, 1 track

rCount1 = 'inf'
rCount2 = 'once'

jump1 = 'next'
jump2 = 'first'

transferList = [[name1, deadTimeData, rCount1, jump1], 
    [name2, pulseData, rCount2, jump2]]

i = 1
for name, data, count, jump in transferList:
    awg.write('wlist:waveform:new "{}", {}'.format(name, recordLength))
    stringArg = 'wlist:waveform:data "{}", 0, {}, '.format(name, recordLength)
    awg.write_binary_values(stringArg, data)
    awg.query('*opc?')
    awg.write('slist:seq:step{}:tasset1:wav "{}", "{}"'.format(i,seqName,name))
    awg.write('slist:seq:step{}:tasset2:wav "{}", "{}"'.format(i,seqName,name))
    awg.write('slist:seq:step{}:rcount "{}", {}'.format(i, seqName, count))
    awg.write('slist:seq:step{}:ejinput "{}", atrigger'.format(i, seqName))
    awg.write('slist:seq:step{}:ejump "{}", {}'.format(i, seqName, jump))
    awg.write('slist:seq:step{}:goto "{}", {}'.format(i, seqName, jump))
    i += 1

awg.write('clock:srate {}'.format(sampleRate))
awg.write('source1:casset:sequence "{}", 1'.format(seqName))
awg.write('source2:casset:sequence "{}", 2'.format(seqName))
awg.write('output1:state on')
awg.write('output2:state on')
awg.write('awgcontrol:run:immediate')
awg.query('*opc?')

delay = ['100ps', '80ps', '60ps', '40ps', '20ps', '0ps', 
    '-20ps', '-40ps', '-60ps', '-80ps', '-100ps']

for d in delay:
    awg.write('source1:skew {}'.format(d))
    awg.write('trigger:immediate atrigger')

print(awg.query('system:error:all?'))
awg.close()
