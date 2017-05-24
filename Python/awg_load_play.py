"""
VISA: AWG Waveform Loader
Author: Morgan Allison
Date created: 1/17
Date edited: 1/17
This program loads a waveform into the instrument, assigns the waveform
to CH1, and plays out the waveform
Windows 7 64-bit
Python 3.5.2 64-bit (Anaconda 4.2.0)
NumPy 1.11.2
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy
"""

import visa
import time


"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
# awg = rm.open_resource('GPIB8::1::INSTR')
awg.timeout = 10000
awg.write('*rst')
awg.write('*cls')

print(scope.query('*idn?'))
scope.write('*rst')
scope.write('*cls')


"""#################CONFIGURE INSTRUMENT#################"""
# to load a .awgx file, you need to use mmemory:open:setup and ensure that
# the path to the setup file is contained in double quotes
setupFile = '"C:\\Users\\mallison\\Desktop\\Tek\\!SAPL\\!AWG\\Waveform Files\\test.awgx"'
awg.write('mmemory:open ', setupFile)
awg.query('*opc?')

# to load a .wfmx file, you need to use mmemory:open and ensure that
# the path to the waveform file is contained in double quotes
wfmFile = '"C:\\Users\\mallison\\Desktop\\Tek\\!SAPL\\!AWG\\Waveform Files\\vec_dl_short_I.wfmx"'
awg.write('mmemory:open ', wfmFile)
awg.query('*opc?')

# to assign a waveform from the waveform list to a channel, use 
# source:casset:waveform
wfmName = awg.query('wlist:name? 1')
awg.write('source1:casset:waveform ', wfmName)
sqcName = '"100MHz 10M QPSK Impaired"'
awg.query('*opc?')

awg.write('awgcontrol:run:immediate')
awg.write('output1:state on')
print(awg.query('system:error:all?'))


t1 = time.perf_counter()
scope.query('*opc?')
t2 = time.perf_counter()
print('Time between output and trigger: {}'.format(t2-t1))

awg.close()
