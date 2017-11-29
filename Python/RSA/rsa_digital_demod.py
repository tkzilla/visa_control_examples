"""
VISA: RSA Digital Demod
Author: Morgan Allison
Updated: 11/17
This program sets up RSA5k/SignalVu-PC/SignalVu remotely to acquire and
demodulate a 3.84 MHz QPSK signal with RRC filter and alpha of 0.22.
Windows 7 64-bit, TekVISA 4.0.4, Python 3.6.3 64-bit
MatPlotLib 2.1.0, PyVISA 1.8
To get PyVISA: pip install pyvisa
Download Anaconda: http://continuum.io/downloads
Anaconda includes MatPlotLib
Download SignalVu-PC programmer manual:
https://www.tek.com/product-software-series/signalvu-pc-manual/signalvu-pc-1
Download RSA5100B programmer manual:
http://www.tek.com/spectrum-analyzer/inst5000-manual-7
Tested on RSA306B, RSA507A, and RSA5126B
Tested on RSA306B, RSA5126B and DPO77002SX with SignalVu
"""

import visa
import matplotlib.pyplot as plt


def dpo_signalvu_check(instId):
    """Check if instrument is an oscilloscope and activate SignalVu if it is"""
    """IMPORTANT: make sure SignalVu is already running if you're using a scope.
       The application:activate command gives focus to SignalVu.
       *OPC? does not respond to application:activate, so there's no good
       way to synchronize this command."""
    if 'MSO' in instId or 'DPO' in instId:
        print('Configuring SignalVu on instrument.')
        inst.write('application:activate \"SignalVu Vector Signal Analysis Software\"')

        # Undocumented commands to control sample rate directly
        sampleRate = 12.5e9
        inst.write('sense:signalvu:acquisition:control:sample:rate off')
        inst.write('sense:signalvu:acquisition:digitizer:sample:rate {}'.format(
            sampleRate))


"""#################SEARCH/CONNECT#################"""
rm = visa.ResourceManager()
# inst = rm.open_resource('TCPIP::192.168.1.11::INSTR')
inst = rm.open_resource('GPIB8::1::INSTR')
inst.timeout = 25000
inst.encoding = 'latin_1'
inst.write_termination = None
inst.read_termination = '\n'
instId = inst.query('*idn?')
print('Connected to', instId)
dpo_signalvu_check(instId)

# preset, clear buffer, and stop acquisition
inst.write('system:preset')
inst.write('*cls')
inst.write('abort')

"""#################CONFIGURE INSTRUMENT#################"""
freq = 2.4453e9
span = 40e6
refLevel = 0

# Set up spectrum acquisition parameters.
inst.write('spectrum:frequency:center {}'.format(freq))
inst.write('spectrum:frequency:span {}'.format(span))
inst.write('input:rlevel {}'.format(refLevel))

# Open new displays.
inst.write('display:ddemod:measview:new conste')    # Constellation
inst.write('display:ddemod:measview:new stable')    # symbol table
inst.write('display:ddemod:measview:new evm')       # EVM vs Time

# Turn off trigger and disable continuous capture (enable single shot mode)
inst.write('initiate:continuous off')
inst.write('trigger:status off')

# Configure digital demod (QPSK, 3.84 MSym/s, RRC/RC filters, alpha 0.22).
symRate = 3.84e6
alpha = 0.22

inst.write('sense:ddemod:modulation:type qpsk')
inst.write('sense:ddemod:srate {}'.format(symRate))
inst.write('sense:ddemod:filter:measurement rrcosine')
inst.write('sense:ddemod:filter:reference rcosine')
inst.write('sense:ddemod:filter:alpha {}'.format(alpha))
inst.write('sense:ddemod:symbol:points one')
# inst.write('sense:ddemod:analysis:length 20000')
# print(inst.query('sense:acquisition:samples?'))

"""#################ACQUIRE DATA#################"""
# Start acquisition.
inst.write('initiate:immediate')
inst.query('*opc?')

# Get constellation display results (details in programmer manual).
results = inst.query('fetch:conste:results?')

# Get EVM vs time data.
evmVsTime = inst.query_binary_values('fetch:evm:trace?')

# Remove terminating whitespace (.rstrip()), split the string result (.split())
# into an array of 3 values, and convert those values to floats.
results = results.rstrip().split(',')
evm = [float(value) for value in results]

"""#################PLOT DATA#################"""
# Print out the results.
# See Python's format spec docs for more details: https://goo.gl/YmjGzV.
print('EVM (RMS): {0[0]:2.3f}%, EVM (peak): {0[1]:2.3f}%, Symbol: {0[2]:<4.0f}'
      .format(evm))

plt.plot(evmVsTime)
plt.title('EVM vs Symbol #')
plt.xlabel('Symbol')
plt.ylabel('EVM (%)')
plt.tight_layout()
plt.show()

inst.close()
