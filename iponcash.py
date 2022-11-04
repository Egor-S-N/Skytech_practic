from socket import socket
from socket import error
from base64 import b64decode
from base64 import b64encode
import logging


class IpOnCashMachine:

    def connect(self, ip, port, timeout): # подключение 
        self.sock = socket()
        self.sock.settimeout(30)
        self.logger = logging.getLogger('IpOnCashMachine')
        self.logger.debug("Connect to {}:{}".format(ip, port))
        self.sock.settimeout(timeout)
        rc = self.sock.connect_ex((ip, port))
        return rc

    def disconnect(self): # отключение 
        self.logger.debug("Disconnect")
        self.sock.close()

    def write(self, data, timeout): # отправка на порт 
        self.logger.debug("Write {} bytes".format(len(data)))
        self.sock.settimeout(timeout)
        try:
            self.sock.sendall(b64decode(data))
            return 0
        except error:
            return -1

    def read(self, size, timeout): # чтение с порта 
        self.logger.debug("Read {} bytes".format(size))
        self.sock.settimeout(timeout)

        try:
            data = self.sock.recv(size)
            return str(b64encode(data), 'UTF-8')
        except error:
            return ''
