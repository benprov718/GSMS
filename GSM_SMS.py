# -*- coding: utf-8 -*-

from __future__ import print_function
import itertools
import sys

__author__ = "Martin Hodný"
__version__ = "0.9.3"


def bin_2_hex(binary=None, length=0):
    return hex(int(binary, 2))[2:].rjust(length, '0')


def hex_2_bin(input_hex=None, length=0):
    return bin(int(input_hex, 16))[2:].rjust(length, '0')


def splitter(iterable_input):
    for i in iterable_input:
        yield i


def grouper(data=None, size=1, join=False):
    a = splitter(data)
    while True:
        b = list(itertools.islice(a, 0, size))
        if not b:
            break
        if not join:
            yield b
        else:
            yield ''.join(b)


class GsmCoder:
    def __init__(self):
        self.gsm = ("@£$¥èéùìòÇ\nØø\rÅåΔ_ΦΓΛΩΠΨΣΘΞ\x1bÆæßÉ !\"#¤%&'()*+,-./0123456789:;<=>?"
                    "¡ABCDEFGHIJKLMNOPQRSTUVWXYZÄÖÑÜ`¿abcdefghijklmnopqrstuvwxyzäöñüà")
        self.ext = ("````````````````````^```````````````````{}`````\\````````````[~]`"
                    "|````````````````````````````````````€``````````````````````````")
        self.encoding = 'GSM'  # or UCS2 (UTF-12-be)

        if sys.version_info.major == 2:  # fix utf8 vs bytestring in Python 2   
            self.gsm = self.gsm.decode('utf8')
            self.ext = self.ext.decode('utf8')

    def encode(self, text):  # input is ascii sentence
        if self.encoding == 'GSM':
            if sys.version_info.major == 2:  # fix utf8 vs bytestring in Python 2
                text = text.decode('UTF8')

            for i in text:
                index = self.gsm.find(i)
                if index > -1:
                    yield bin(index)[2:].rjust(7, '0')
                else:
                    index = self.ext.find(i)
                    if index > -1:
                        yield hex_2_bin('1B', length=7)
                        yield bin(index)[2:].rjust(7, '0')
                    else:
                        yield bin(self.gsm.find('.')).rjust(7, '0')
        elif self.encoding == 'UCS2':
            print("Not supported characters by GSM encoding, switching to UCS2.")
            for i in text.encode('UTF-16-be'):
                yield hex_2_bin(hex(i), length=2)

    def decode(self, binary):  # input is 7bit binary list
        extension = False
        for i in binary:
            index = int(i, 2)
            if index != 27:
                if extension:
                    yield (self.ext[index])
                    extension = False
                else:
                    yield (self.gsm[index])
            else:
                extension = True

    def text_2_gsm(self, text):
        for i in text:
            if not (i in self.gsm or i in self.ext):
                self.encoding = 'UCS2'
        result = []
        if self.encoding == 'GSM':
            for buffer in grouper(data=self.encode(text), size=8, join=False):
                appendix = []
                for index, binary in enumerate(buffer):
                    if index + 1 < len(buffer):
                        appendix.append(buffer[index + 1][-(index + 1):])
                        result.append(
                            bin_2_hex(('%s%s' % (appendix[index], binary[:-index] if index > 0 else binary)), length=2))
                if index != 7:
                    if index > 0:
                        result.append(bin_2_hex(binary[:-index], length=2))
                    else:
                        result.append(bin_2_hex(binary, length=2))
            return ''.join(result)
        elif self.encoding == 'UCS2':
            hexa = []
            for i in text.encode('UTF-16-be'):
                if sys.version_info.major == 2:
                    hexa.append(i.encode('hex'))
                else:
                    hexa.append((hex(i)[2:].rjust(2, '0')))
            return ''.join(hexa)

    def gsm_2_text(self, hexa):
        result = []
        if self.encoding == 'GSM':
            for buffer in grouper(data=hexa, size=14, join=False):  # split by 7 byte
                rest = []
                for index, i in enumerate(grouper(data=buffer, size=2, join=True)):  # split by hex
                    binary = hex_2_bin(i, 8)
                    rest.append(binary[:index + 1])
                    result.append('%s%s' % (binary[index + 1:], rest[index - 1] if index > 0 else ''))
                    if index == 6 and rest[index] != '0000000':
                        result.append('%s' % rest[index])
            return ''.join(list(self.decode(result)))
        elif self.encoding == 'UCS2':
            utf_encoded = bytearray.fromhex(''.join(hexa))
            return utf_encoded.decode('UTF-16-be')
            pass

if __name__ == "__main__":
    gsm = GsmCoder()

    if sys.version_info.major == 2:
        sms_hexa = gsm.text_2_gsm("How much € {Euro} does it cost, some ugly characters ~ccažěščřžýáíé".decode('UTF8'))
    else:
        sms_hexa = gsm.text_2_gsm("How much € {Euro} does it cost, some ugly characters ~ccažěščřžýáíé")

    print("sms_hexa: ", sms_hexa)
    sms_text = gsm.gsm_2_text(sms_hexa)
    print("sms_test: ", sms_text)



