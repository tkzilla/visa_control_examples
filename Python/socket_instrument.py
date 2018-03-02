"""
Socket Instrument Class
Author: Morgan Allison
Based on awg70k_sock.py, written by Carl Murdock
Updated: 03/18
This program provides a socket interface to Tektronix test equipment.
It handles sending commands, receiving query results, and
reading binary block data.
Windows 7 64-bit, TekVISA 4.0.4 and 4.2.15 (AWG only)
Python 3.6.3 64-bit
NumPy 1.13.3
Tested on RSA5126B, RSA7100A, RSA507A + SignalVu-PC,
DPO77002SX, MSO58,
AWG70002A, AWG5208
"""

import socket
import numpy as np


class BinblockError(Exception):
    """Binary Block Exception class"""
    pass


class SockInstError(Exception):
    """Socket Instrument Exception class"""
    pass


class SocketInstrument:
    def __init__(self, host, port, timeout=10):
        """Open socket connection with settings for instrument control."""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.socket.settimeout(timeout)
        self.socket.connect((host, port))

        self.instId = self.query('*idn?')

    def disconnect(self):
        """Gracefully close connection."""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def query(self, cmd):
        """Sends query to instrument and returns reply as string."""
        # self.write(cmd)

        msg = '{}\n'.format(cmd)
        self.socket.send(msg.encode('latin_1'))

        # Read continuously until termination character is found.
        response = b''
        while response[-1:] != b'\n':
            response += self.socket.recv(1024)

        # Strip out whitespace and return.
        return response.decode('latin_1').strip()

    def write(self, cmd):
        """Write a command string to instrument."""
        # msg = '{}\n'.format(cmd)
        # self.socket.send(msg.encode('latin_1'))
        msg = '{}\n*esr?'.format(cmd)
        ret = self.query(msg)
        if (int(ret) != 0):
            raise SockInstError('esr non-zero: {}'.format(ret))

    def binblockread(self, dtype=np.int8, debug=False):
        """Read data with IEEE 488.2 binary block format

        The waveform is formatted as:
        #<x><yyy><data><newline>, where:
        <x> is the number of y bytes. For example, if <yyy>=500, then <x>=3.
        NOTE: <x> is a hexadecimal number.
        <yyy> is the number of bytes to transfer. Care must be taken
        when selecting the data type used to interpret the data.
        The dtype argument used to read the data must match the data
        type used by the instrument that sends the data.
        <data> is the curve data in binary format.
        <newline> is a single byte new line character at the end of the data.
        """

        # Read # character, raise exception if not present.
        if self.socket.recv(1) != b'#':
            raise BinblockError('Data in buffer is not in binblock format.')

        # Extract header length and number of bytes in binblock.
        headerLength = int(self.socket.recv(1).decode('latin_1'), 16)
        numBytes = int(self.socket.recv(headerLength).decode('latin_1'))

        if debug:
            print('Header: #{}{}'.format(headerLength, numBytes))

        rawData = bytearray(numBytes)
        buf = memoryview(rawData)

        # While there is data left to read...
        while numBytes:
            # Read data from instrument into buffer.
            bytesRecv = self.socket.recv_into(buf, numBytes)
            # Slice buffer to preserve data already written to it.
            buf = buf[bytesRecv:]
            # Subtract bytes received from total bytes.
            numBytes -= bytesRecv
            if debug:
                print('numBytes: {}, bytesRecv: {}'.format(
                    numBytes, bytesRecv))

        # Receive termination character.
        term = self.socket.recv(1)
        if debug:
            print('Term char: ', term)
        # If term char is incorrect or not present, raise exception.
        if term != b'\n':
            print('Term char: {}, rawData Length: {}'.format(
                term, len(rawData)))
            raise BinblockError('Data not terminated correctly.')

        # Convert binary data to NumPy array of specified data type and return.
        return np.frombuffer(rawData, dtype=dtype)

    def binblock_header(self, data):
        """Returns a IEEE 488.2 binary block header

        #<x><yyy>..., where:
        <x> is the number of y bytes. For example, if <yyy>=500, then <x>=3.
        NOTE: <x> is a hexadecimal number.
        <yyy> is the number of bytes to transfer. """

        numBytes = memoryview(data).nbytes
        return f'#{len(str(numBytes))}{numBytes}'

    def binblockwrite(self, msg, data, debug=False):
        """Send data with IEEE 488.2 binary block format

        The data is formatted as:
        #<x><yyy><data><newline>, where:
        <x> is the number of y bytes. For example, if <yyy>=500, then <x>=3.
        NOTE: <x> is a hexadecimal number.
        <yyy> is the number of bytes to transfer. Care must be taken
        when selecting the data type used to interpret the data.
        The dtype argument used to read the data must match the data
        type used by the instrument that sends the data.
        <data> is the curve data in binary format.
        <newline> is a single byte new line character at the end of the data.
        """

        header = self.binblock_header(data)

        # Send message, header, data, and termination
        self.socket.send(msg.encode('latin_1'))
        self.socket.send(header.encode('latin_1'))
        self.socket.send(data)
        self.socket.send(b'\n')

        if debug:
            print(f'binblockwrite --')
            print(f'msg: {msg}')
            print(f'header: {header}')

        # Check error status register and notify of problems
        r = self.query('*esr?')
        if int(r) is not 0:
            raise BinblockError(f'Non-zero ESR: {r}')
        pass

    def wfm_writer(self, name, data, debug=False):
        """Helper function for writing waveform data to AWGs"""
        blockData = memoryview(data)
        numSamples, err = divmod(blockData.nbytes, 4)
        if err is not 0:
            raise BinblockError('Total waveform data must be a multiple of 4 bytes.')
        # The maximum write size of wlist:waveform:data is 250 MSamples (1 GB)
        maxWrite = 249999999
        if blockData.nbytes < maxWrite:  # If waveform is small enough, one write
            self.binblockwrite(f'wlist:waveform:data "{name}", 0,', blockData, debug)
        else:   # If it's too big, multiple writes are required
            for offset in range(0, numSamples, maxWrite):
                partialData = blockData[offset:offset + maxWrite]
                self.binblockwrite(f'wlist:waveform:data "{name}", {offset},', partialData, debug)


def awg_example(ipAddress, port):
    """Tests generic waveform transfer to AWG.

    The AWG's native data type is 32 bit floating point.
    Format and send your waveforms as float32 to ensure compatibility.

    NOTE: This only works for standalone AWGs, not SourceXpress.
    TekVISA's socket server has some flaws when acting as a client
    for receiving large binary blocks. The older AWG instruments
    use Socket Server Plus, which is much more robust.
    TekVISA socket server uses port 4000
    Socket Server Plus uses port 4001"""

    awg = SocketInstrument(host=ipAddress, port=port, timeout=10)
    print(awg.instId)
    awg.query('*esr?')
    print(awg.query('system:error:all?'))

    # awg.write('*rst')
    # from time import sleep
    # sleep(7)  # the AWG takes ~7 seconds to default...
    # awg.query('*opc?')

    wfmName = 'test'
    wfmLength = 10e6
    wfmData = np.sin(np.linspace(0, 2 * np.pi, wfmLength), dtype=np.float32)

    awg.write('wlist:waveform:delete all')
    awg.write(f'wlist:waveform:new "{wfmName}", {wfmLength}')
    awg.wfm_writer(wfmName, wfmData)
    awg.write(f'source1:casset:waveform "{wfmName}"')
    awg.write('awgcontrol:run:immediate')
    awg.query('*opc?')
    awg.write('output1 on')

    awg.query('*esr?')
    print(awg.query('system:error:all?'))

    awg.disconnect()


def rsa_example(ipAddress):
    """Test generic RSA connection, signal capture, and data transfer."""
    rsa = SocketInstrument(host=ipAddress, port=4000, timeout=3)
    print(rsa.instId)

    rsa.write('system:preset')
    rsa.write('initiate:continuous off')
    rsa.write('sense:spectrum:points:count P64001')
    for i in range(10):
        rsa.write('initiate:immediate')
        rsa.query('*opc?')
        rsa.write('fetch:spectrum:trace?')
        data = rsa.binblockread(dtype=np.float32, debug=True)

    rsa.query('*esr?')
    print(rsa.query('system:error:all?'))
    rsa.disconnect()
    return data


def scope_example(ipAddress):
    """Test generic scope connection, signal capture, and data transfer."""
    dpo = SocketInstrument(host=ipAddress, port=4000, timeout=3)
    print(dpo.instId)

    dpo.write('*rst')
    dpo.write('acquire:stopafter sequence')
    rl = dpo.query('horizontal:mode:recordlength?')
    dpo.write('data:stop {}'.format(rl))

    for i in range(10):
        dpo.write('acquire:state on')
        dpo.query('*opc?')

        dpo.write('curve?')
        data = dpo.binblockread(dtype=np.uint8, debug=True)

    dpo.query('*esr?')
    print(dpo.query('allev?'))

    dpo.disconnect()
    return data


def main():
    awg_example('127.0.0.1', port=4000)
    # rsa_example('127.0.0.1')
    # scope_example('192.168.1.84', port=4000)


if __name__ == '__main__':
    main()
