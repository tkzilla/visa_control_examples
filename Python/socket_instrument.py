"""
Socket Instrument Class
Author: Morgan Allison
Based on awg7k_sock.py, written by Carl Murdock
Updated: 11/17
This program provides a socket interface to Tektronix test equipment.
It handles sending commands, receiving query results, and
reading binary block data.
Windows 7 64-bit, TekVISA 4.0.4
Python 3.6.2 64-bit
NumPy 1.13.3
Tested on RSA5126B, RSA7100A, DPO77002SX, RSA507A + SignalVu-PC, MSO58
"""

import socket
import numpy as np


class BinblockError(Exception):
    """Binary Block Exception class"""
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
        self.write(cmd)

        # Read continuously until termination character is found.
        response = b''
        while response[-1:] != b'\n':
            response += self.socket.recv(1024)

        # Strip out whitespace and return.
        return response.decode().strip()

    def write(self, cmd):
        """Write a command string to instrument."""
        msg = '{}\n'.format(cmd)
        self.socket.send(msg.encode('latin_1'))

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
        buffer = memoryview(rawData)

        # While there is data left to read...
        while numBytes:
            # Read data from instrument into buffer.
            bytesRecv = self.socket.recv_into(buffer, numBytes)
            # Slice buffer to preserve data already written to it.
            buffer = buffer[bytesRecv:]
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

    def binblockwrite(self):
        """TODO"""
        print('Not implemented.')


def rsa_example(ipAddress):
    """Test generic RSA connection, signal capture, and data transfer."""
    inst = SocketInstrument(host=ipAddress, port=4000, timeout=3)
    print(inst.instId)

    inst.write('system:preset')
    inst.write('initiate:continuous off')
    inst.write('sense:spectrum:points:count P64001')
    for i in range(10):
        inst.write('initiate:immediate')
        inst.query('*opc?')
        inst.write('fetch:spectrum:trace?')
        data = inst.binblockread(dtype=np.float32, debug=True)

    inst.query('*esr?')
    print(inst.query('system:error:all?'))

    inst.disconnect()
    return data


def scope_example(ipAddress):
    """Test generic scope connection, signal capture, and data transfer."""
    inst = SocketInstrument(host=ipAddress, port=4000, timeout=3)
    print(inst.instId)

    inst.write('*rst')
    inst.write('acquire:stopafter sequence')
    rl = inst.query('horizontal:mode:recordlength?')
    inst.write('data:stop {}'.format(rl))

    for i in range(10):
        inst.write('acquire:state on')
        inst.query('*opc?')

        inst.write('curve?')
        data = inst.binblockread(dtype=np.uint8, debug=True)

    inst.query('*esr?')
    print(inst.query('allev?'))

    inst.disconnect()
    return data


def main():
    scope_example('192.168.1.8')


if __name__ == '__main__':
    main()
