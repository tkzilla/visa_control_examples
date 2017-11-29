"""
VISA: MDO RF vs Time Mask Test
Author: Morgan Allison
Updated: 11/17
This program captures an RF vs Time trace and allows the user to build
a mask for that trace and test for violations.
Windows 7 64-bit, TekVISA 4.0.4
Python 3.6.0 64-bit (Anaconda 4.3.0)
NumPy 1.11.2, MatPlotLib 2.0.0, PyVISA 1.8
To get PyVISA: pip install pyvisa
Download Anaconda: http://continuum.io/downloads
Anaconda includes NumPy and MatPlotLib
Tested on MDO4104B-6
"""

import visa
import numpy as np
import matplotlib.pyplot as plt


class MDO:
    def __init__(self, instID, timeout=25000):
        self.inst = visa.ResourceManager().open_resource(instID)
        self.inst.timeout = timeout
        self.inst.encoding = 'latin_1'
        self.inst.write_termination = None
        self.inst.read_termination = '\n'

        print('Connected to ', self.inst.query('*IDN?'))
        self.inst.write('*RST')
        self.inst.write('*CLS')

    def setup(self, cf, span, trigLevel, vScale, hScale, hPos=10):
        """Configures scope for simulatenous RF and time domain analysis"""
        self.inst.write('rf:frequency {}'.format(cf))
        self.inst.write('rf:span {}'.format(span))
        self.inst.write('horizontal:scale {}'.format(hScale))
        self.inst.write('horizontal:delay:mode 0')
        self.inst.write('horizontal:position {}'.format(hPos))
        self.inst.write('select:rf_amplitude on')
        self.inst.write('rf:rf_amplitude:vertical:scale {}'.format(vScale))
        self.inst.write('trigger:a:edge:source rf')
        self.inst.write('trigger:a:logic:threshold:rf {}'.format(trigLevel))
        self.inst.write('data:source rf_amplitude')

    def get_waveform_info(self):
        """Gather waveform transfer information from scope."""
        self.inst.write('acquire:stopafter sequence')
        self.inst.write('acquire:state on')
        self.inst.query('*OPC?')

        # dType is a single format character from Python's struct module
        # https://docs.python.org/2/library/struct.html#format-characters
        encoding = self.inst.query('data:encdg?').rstrip()
        if 'RIB' in encoding or 'FAS' in encoding:
            self.dType = 'b'
            self.bigEndian = True
        elif 'RPB' in encoding:
            self.dType = 'B'
            self.bigEndian = True
        elif 'SRI' in encoding:
            self.dtype = 'b'
            self.bigEndian = False
        elif 'SRP' in encoding:
            self.dtype = 'B'
            self.bigEndian = False
        elif 'FP' in encoding:
            self.dType = 'f'
            self.bigEndian = True
        elif 'SFP' in encoding:
            self.dType = 'f'
            self.bigEndian = False
        elif 'ASCI' in encoding:
            raise visa.InvalidBinaryFormat('ASCII Formatting.')
        else:
            raise visa.InvalidBinaryFormat

        self.numPoints = int(self.inst.query('wfmoutpre:nr_pt?'))
        self.xIncr = float(self.inst.query('wfmoutpre:xincr?'))
        self.yMult = float(self.inst.query('wfmoutpre:ymult?'))
        self.yOff = float(self.inst.query('wfmoutpre:yoff?'))

        # self.inst.write('header on')
        # print(self.inst.query('wfmoutpre?'))
        # self.inst.write('header off')

    def get_waveform(self):
        """Get waveform from scope and scale correctly"""
        self.wfm = self.inst.query_binary_values('curve?', datatype=self.dType,
            is_big_endian=self.bigEndian, container=np.array)
        self.wfm = (self.wfm - self.yOff) * self.yMult

    def create_mask(self, xMargin, yMargin, pAmp, pWidth, rTime, fTime):
        """Creates a waveform mask based on x and y margins"""
        self.upperMask = np.zeros(self.numPoints)
        self.lowerMask = np.zeros(self.numPoints)

        pWidth = int(pWidth / self.xIncr)
        rTime = int(rTime / self.xIncr)
        fTime = int(fTime / self.xIncr)
        xMargin = int(xMargin / self.xIncr)
        hPos = 25
        trigPoint = int(self.numPoints * hPos / 100)

        try:
            prePulse = int(trigPoint - xMargin - rTime / 2)
            postPulse = int(trigPoint + pWidth + xMargin + rTime / 2 + fTime)
            self.upperMask[:prePulse] = yMargin
            if rTime > 0:
                self.upperMask[prePulse:prePulse + rTime] = np.linspace(
                    yMargin, pAmp + yMargin, rTime)
                self.upperMask[prePulse + rTime:postPulse] = pAmp + yMargin
            else:
                self.upperMask[prePulse:postPulse] = pAmp + yMargin
            if fTime > 0:
                self.upperMask[postPulse - fTime:postPulse] = np.linspace(
                    pAmp + yMargin, yMargin, fTime)
                self.upperMask[postPulse:] = yMargin
            else:
                self.upperMask[prePulse + rTime:postPulse] = pAmp + yMargin
                self.upperMask[postPulse:] = yMargin
        except ValueError as err:
            print(str(err))

        prePulse = int(trigPoint + xMargin - rTime / 2)
        postPulse = int(trigPoint + pWidth + rTime / 2 + fTime - xMargin)
        self.lowerMask[:prePulse] = -yMargin
        if rTime > 0:
            self.lowerMask[prePulse:prePulse + rTime] = np.linspace(
                -yMargin, pAmp - yMargin, rTime)
            self.lowerMask[prePulse + rTime:postPulse] = pAmp - yMargin
        else:
            self.lowerMask[prePulse:postPulse] = pAmp - yMargin

        if fTime > 0:
            self.lowerMask[postPulse - fTime:postPulse] = np.linspace(
                pAmp - yMargin, -yMargin, fTime)
            self.lowerMask[postPulse:] = -yMargin
        else:
            self.lowerMask[prePulse + rTime:postPulse] = pAmp - yMargin
            self.lowerMask[postPulse:] = -yMargin

        self.trigPoint = trigPoint

    def test_mask(self):
        """Tests the waveform against the created mask and tracks failures"""
        self.failIndex = []
        for i in range(len(self.wfm)):
            if (self.upperMask[i] - self.wfm[i] < 0) or (self.wfm[i] - self.lowerMask[i] < 0):
                self.failIndex.append(i)

    def plot_masks(self):
        """Overlays upper and lower masks on RF vs time waveform"""
        time = np.linspace(0, self.numPoints * self.xIncr, self.numPoints)
        plt.figure(1, figsize=(10, 5))
        ax1 = plt.subplot(211, facecolor='k')
        ax1.plot(time, self.wfm, color='orange')
        ax1.set_title('RF Amplitude vs Time')
        ax1.set_xlabel('Time (sec)')
        ax1.set_ylabel('Amplitude (V)')
        ax1.axvline(time[self.trigPoint], color='orange')
        ax2 = plt.subplot(212, facecolor='k')
        ax2.plot(time, self.wfm, color='orange')
        ax2.plot(time, self.upperMask, color='red')
        ax2.plot(time, self.lowerMask, color='red')
        ax2.set_title('RF Amplitude vs Time')
        ax2.set_xlabel('Time (sec)')
        ax2.set_ylabel('Amplitude (V)')
        for index in self.failIndex:
            ax2.axvline(time[index], color='white')
        plt.tight_layout()
        plt.show()


def main():
    # basic setup
    cf = 1e9            # Hz
    span = 100e6        # Hz
    trigLevel = -20     # dBm
    vScale = 20e-3      # V
    hPos = 25           # %
    hScale = 4e-6       # sec/div

    # margins
    xMargin = 1e-6      # sec
    yMargin = 20e-3     # V

    # ideal pulse mask
    pAmp = 0.126        # Vrms
    pWidth = 10e-6      # sec
    rTime = 1e-6        # sec
    fTime = 1e-6    # sec

    mdo = MDO('TCPIP::192.168.1.66::INSTR')
    mdo.setup(cf, span, trigLevel, vScale, hScale, hPos)
    mdo.get_waveform_info()
    mdo.get_waveform()
    mdo.create_mask(xMargin, yMargin, pAmp, pWidth, rTime, fTime)
    mdo.test_mask()
    mdo.plot_masks()

    mdo.inst.close()


if __name__ == '__main__':
    main()
