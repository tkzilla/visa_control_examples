"""
VISA Control: RSA Mask Test Query
Author: Morgan Allison
Updated: 11/17
Sets up a default mask test and queries the frequencies
at which violations occured.
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

# Configure new displays
rsa.write('display:general:measview:new dpx')
rsa.write('spectrum:frequency:center {}'.format(cf))
rsa.write('spectrum:frequency:span {}'.format(span))

# Configure mask test
rsa.write('calculate:search:limit:match:beep on')
rsa.write('calculate:search:limit:match:sacquire off')
rsa.write('calculate:search:limit:match:sdata off')
rsa.write('calculate:search:limit:match:spicture off')
rsa.write('calculate:search:limit:match:strace off')
rsa.write('calculate:search:limit:operation omask')
rsa.write('calculate:search:limit:operation:feed "dpx", "Trace1"')
rsa.write('calculate:search:limit:state on')


"""#################ACQUIRE DATA#################"""
rsa.write('initiate:immediate')
rsa.query('*opc?')

# Query and print mask violations
if int(rsa.query('calculate:search:limit:fail?').strip()) == 1:
    maskPoints = rsa.query('calculate:search:limit:report:data?')
    # print(maskPoints)
    maskPoints = [m.replace('"', '') for m in maskPoints.strip().split(',"')]
    print('Mask Violations: {}'.format(maskPoints[0]))
    for m in maskPoints[1:]:
        print('Violation Range: {}'.format(m))
else:
    print('No mask violations have occurred.')

rsa.close()
