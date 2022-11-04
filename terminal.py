import serial
import logging


tagUnEncrypted = (bytes([0x1F, 0x84, 0x00]))
tagContainer = (bytes([0x3F, 0x6E]))


def bytesConsume(intVariable): # потребление байтов 
    bytesConsume = 0
    while intVariable != 0:
        intVariable >>= 8
        bytesConsume += 1
    return bytesConsume

class TlvMessage:
    def __init__(self):
        self.package_number = 0 # номер 
        self.package_count = 0 # длинна данных
        self.message = str() # данные 

    def setMessage(self, message):
        self.message = message

    def setPackageNumber(self, number):
        self.package_number = number

    def setPackageCount(self, count):
        self.package_count = count


class Terminal:
    def __init__(self, port):
        self.ser = serial.Serial(port)
        self.ser.baudrate = 115200
        self.ser.bytesize = serial.EIGHTBITS
        self.logger = logging.getLogger('CashToTerminal')
    
    def readLength(self): 
        lenByte = int.from_bytes(self.ser.read(1), byteorder='big', signed=False)
        if(lenByte < 0x80):
            return lenByte
        else:
            length = int.from_bytes(self.ser.read(lenByte - 0x80), byteorder='big', signed=False)
            return length

    def parseLength(self, data):
        lenByte = int.from_bytes(data[:1], byteorder='big', signed=False)
        skip_length = 1
        if(lenByte < 0x80):
            return lenByte, skip_length
        else:
            bytes_to_read = lenByte - 0x80
            skip_length += bytes_to_read
            length = int.from_bytes(data[1:bytes_to_read+1], byteorder='big', signed=False)
            return length, skip_length


    def parsePackage(self, data):
        t = TlvMessage()
        parsed = 0
        while(parsed < len(data)):
            tag = data[parsed+2:parsed+3]
            parsed+= 3
            if tag == bytes('\x44', 'utf-8'):
                data_len, skip_len = self.parseLength(data[parsed:])
                parsed+= skip_len
                t.package_count = int.from_bytes(data[parsed:parsed+data_len], byteorder='little', signed=False)
                parsed += data_len
                continue

            if tag == bytes('\x43', 'utf-8'):
                data_len, skip_len = self.parseLength(data[parsed:])
                parsed+= skip_len
                t.package_number = int.from_bytes(data[parsed:parsed+data_len], byteorder='little', signed=False)
                parsed += data_len
                continue

            if tag == bytes('\x00', 'utf-8'):
                self.logger.debug('Parse TLV data')
                data_len, skip_len = self.parseLength(data[parsed:])
                self.logger.debug('Data length: {0}'.format(data_len))
                self.logger.debug('Length of length: {0}'.format(skip_len))
                parsed+= skip_len
                t.message = str(data[parsed:parsed+data_len], 'utf-8')
                self.logger.debug('Data: {}'.format(t.message))
                parsed += data_len
                continue

        return t

    def read(self):
        if self.ser.in_waiting > 0:
            header = self.ser.read(2)  # read header. TODO add check for encryption
            self.logger.debug('Header: {0}'.format(header.hex()))
            total_length = self.readLength() # read length of full package
            full_package = self.ser.read(total_length)
            self.logger.debug('Full data:{0}'.format(full_package.hex()))
            tlv = self.parsePackage(full_package)

            self.logger.debug('Package {0} of {1}'.format(tlv.package_number, tlv.package_count))

            message = tlv.message

            if tlv.package_count == 0:
                tlv.package_count = 1

            for i in range(tlv.package_count-1):
                self.logger.debug('Package {0} of {1}'.format(i+2, tlv.package_count))
                self.ser.read(2)  # read header. TODO add check for encryption
                total_length = self.readLength() # read length of full package
                full_package = self.ser.read(total_length)
                tlv = self.parsePackage(full_package)
                
                message += tlv.message
            
            self.logger.debug('Recv:{0}'.format(message))
            return message

        else:
            return ''


    def write(self, data):
        self.logger.debug('Send:{0}'.format(data))
        msg = wrapToTlv(tagUnEncrypted, data)
        self.logger.debug('Package: {}'.format(msg.hex()))
        sentlen = self.ser.write(msg)
        return sentlen

    def read_one_byte(self):
        self.ser.timeout = 0
        self.ser.read(1)
        self.ser.timeout = 60


def wrapToTlv(tag, message):
    messageBytes =  bytes(message, 'utf-8') 
    messageLength = len(messageBytes)

    # count, how many bytes does length tag use
    lenTagBytesAmount = bytesConsume(messageLength)

    # if messageLength > 127 - add special byte
    if messageLength > 0x7f:
        specialByte = (0x80 + lenTagBytesAmount).to_bytes(1, byteorder='big')
        lenTagBytes = specialByte + \
            messageLength.to_bytes(lenTagBytesAmount, byteorder='big')
    else:
        lenTagBytes = messageLength.to_bytes(
            lenTagBytesAmount, byteorder='big')

    # always use only one package
    result = b'\x1F\x84\x44\x04\x01\x00\x00\x00\x1F\x84\x43\x04\x01\x00\x00\x00'+ tag + lenTagBytes + messageBytes

    result_length = len(result)
    lenTagBytesAmount = bytesConsume(result_length)
    if result_length > 0x7f:
        specialByte = (0x80 + lenTagBytesAmount).to_bytes(1, byteorder='big')
        lenTagBytes = specialByte + \
            result_length.to_bytes(lenTagBytesAmount, byteorder='big')
    else:
        lenTagBytes = result_length.to_bytes(
            lenTagBytesAmount, byteorder='big')


    return tagContainer + lenTagBytes + result
