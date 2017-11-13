"""
Socket Instrument Class
Author: Morgan Allison
Based on awg7k_sock.py, written by Carl Murdock
Date edited: 10/17
This program provides a socket interface to Tektronix test equipment.
It handles sending commands, receiving query results, and
reading binary block data.
Windows 7 64-bit, TekVISA 4.0.4
Python 3.6.1 64-bit (Anaconda 4.4.0)
NumPy 1.13.1
Tested on RSA5126B, RSA7100A, DPO77002SX, RSA507A+SignalVu-PC, MSO58
"""

import socket
import numpy as np


class BinblockError(Exception):
    """Binary Block Exception class"""
    pass

class SocketInstrument:
    def __init__(self, host, port, timeout=10):
        """sets up instrument socket"""
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setblocking(False)
        self.socket.settimeout(timeout)
        self.socket.connect((host, port))

        self.instId = self.query('*idn?')

    def disconnect(self):
        """closes connection"""
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()

    def query(self, cmd):
        """Sends query to instrument and returns reply as string"""
        # send message
        self.write(cmd)
        
        # continuously read until termination character is found
        response = b''
        while response[-1:] != b'\n':
            response += self.socket.recv(1024)
        
        # strip out whitespace characters
        return response.decode().strip()

    def write(self, cmd):
        """writes a command string to instrument"""
        msg = '{}\n'.format(cmd)
        self.socket.send(msg.encode('latin_1'))

    def binblockread(self, dtype=np.int8, debug=False):
        """Reads a binary block with format '#<headerLength><numBytes>DATA'
        Returns a NumPy array of the specified data type"""
        
        # Read # character, throw exception if not present
        if self.socket.recv(1) != b'#':
            raise BinblockError('Data in buffer is not in binblock format.')
        
        # Extract header length and number of bytes in binblock
        headerLength = int(self.socket.recv(1).decode('latin_1'), 16)
        numBytes = int(self.socket.recv(headerLength).decode('latin_1'))
        
        if debug:
            print('Header: #{}{}'.format(headerLength, numBytes))
        
        rawData = bytearray(numBytes)
        buffer = memoryview(rawData)
        
        # While there is data left to read
        while numBytes:
            # Read data from instrument into buffer
            bytesRecv = self.socket.recv_into(buffer, numBytes)
            # Slice buffer to preserve data already written to it
            buffer = buffer[bytesRecv:]
            # Subtract bytes read from total bytes
            numBytes -= bytesRecv
            if debug:
                print('numBytes: {}, bytesRecv: {}'.format(numBytes, bytesRecv))

        # Receive termination character
        term = self.socket.recv(1)
        if debug:
            print('Term char: ', term)
        # If term char is incorrect or not present, raise exception
        if term != b'\n':
            print('Term char: {}, rawData Length: {}'.format(term, len(rawData)))
            raise BinblockError('Data not terminated correctly.')
        
        # Convert binary data to NumPy array and return
        return np.frombuffer(rawData, dtype=dtype)

    def get_error(self):
        self.query('*esr?')
        # return self.query('system:error:all?')
        return self.query('allev?')


def rsa_example(ipAddress):
    """This is for testing pretty much any RSA"""
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
    
    print(inst.get_error())
    inst.disconnect()
    return data


def scope_example(ipAddress):
    """This is for testing pretty much any scope"""
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
    
    print(inst.get_error())
    inst.disconnect()
    return data


def main():
    data = scope_example('192.168.1.8')

    
if __name__ == '__main__':
    main()
