"""
VISA: DPX Trace Selector
Author: Morgan Allison
Updated: 11/17
This program opens up a split DPX display and allows the user to select
the available traces. The trace numbers in the VISA commands are interpreted
in the comments below
Windows 7 64-bit, TekVISA 4.0.4, Python 3.6.3 64-bit
PyVISA 1.8
To get PyVISA: pip install pyvisa
To get Anaconda: http://continuum.io/downloads
Download SignalVu-PC programmer manual:
https://www.tek.com/product-software-series/signalvu-pc-manual/signalvu-pc-1
Download RSA5100B programmer manual:
http://www.tek.com/spectrum-analyzer/inst5000-manual-7
Tested on RSA306B, RSA507A, RSA5126B
"""

import visa

"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
# rsa = rm.open_resource('TCPIP::192.168.1.9::INSTR')
rsa = rm.open_resource('GPIB8::1::INSTR')
rsa.timeout = 10000
rsa.encoding = 'latin_1'
rsa.write_termination = None
rsa.read_termination = '\n'
print('Connected to', rsa.query('*idn?'))

rsa.write('*rst')
rsa.write('*cls')
rsa.write('abort')


"""#################CONFIGURE INSTRUMENT#################"""
# Configure acquisition parameters
cf = 2.4453e9
span = 40e6

# Configure DPX measurement
rsa.write('display:general:measview:new DPX')
rsa.write('sense:dpx:plot split')
rsa.write('spectrum:frequency:center {}'.format(cf))
rsa.write('spectrum:frequency:span {}'.format(span))

"""#################ACQUIRE DATA#################"""
rsa.write('initiate:immediate')
rsa.query('*opc?')

rsa.write('trace1:dpx 1')  # Trace 1
rsa.write('trace2:dpx 1')  # Trace 2
rsa.write('trace3:dpx 1')  # Trace 3
rsa.write('trace4:dpx 0')  # Math
rsa.write('trace5:dpx 1')  # Bitmap
rsa.write('trace6:dpx 1')  # DPXogram
rsa.write('trace7:dpx 1')  # DPXogram Line

rsa.close()
