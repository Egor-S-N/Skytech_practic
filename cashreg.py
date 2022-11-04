import json
import datetime
import argparse
import logging
import signal
from iponcash import IpOnCashMachine
from terminal import Terminal

interruptState = 'continue'

def interruptOperation(signum, frame): # прерыв операции 
    if signal.SIGINT == signum:
        global interruptState
        interruptState = 'break'
    

def generateSuccessJson(id): # гененрирует успешный ответ
    jsn = {}
    jsn['jsonrpc'] = '2.0'
    jsn['result'] = 'Success'
    jsn['id'] = str(id)
    return json.dumps(jsn)


def generateErrorJson(id):# гененрирует неверный  ответ
    error = {}
    error['code'] = -32001
    jsn = {}
    jsn['jsonrpc'] = '2.0'
    jsn['error'] = error
    jsn['id'] = str(id)
    return json.dumps(jsn)


def readJsonFromFile(filename): # читает json файл 
    with open(filename, 'r') as myfile:
        data = myfile.read().replace('\n', '')
    return data

def main(port: str, file: str): # ГЛАВНЫЙ ЗАПУСК 
    logging.basicConfig(format='%(asctime)s %(levelname)s %(name)s %(msg)s', level=logging.DEBUG)
    logging.info('Try to open {}'.format(port))

    terminal = Terminal(port)

    

    cashreg_comlink = IpOnCashMachine()

   
    
   
    print(readJsonFromFile(file))
    terminal.write(readJsonFromFile(file))
    signal.signal(signal.SIGINT, interruptOperation)

#     # main loop
    while True:
        data = terminal.read()
        
        if not data:
            continue
        jsn = json.loads(data, strict=False)
        
        

        error = jsn.get('error', '')
        if error != '':
            msg = error['message']
            code = error['code']
            logging.error('Error from terminal {0}({1})'.format(msg, code))
            break

        result = jsn.get('result', '')
        if result != '':
            if result == 'Started':
                # if choice == "9" :  # if Reboot - exit
                #     break
                pass
            elif result == 'OK':
                return(jsn)
                break
            
        method = jsn.get('method', '')

        if method != '':
            if method == 'Result' or method == 'ReconciliationResult':
                terminal.write(generateSuccessJson(jsn['id']))
                terminal.read_one_byte()
                return(jsn)
                
                break

            if method == 'Status':
                terminal.write(generateSuccessJson(jsn['id']))
                continue

            if method == 'Print':
                print(jsn['params'])
                terminal.write(generateSuccessJson(jsn['id']))
                continue

            if method == 'Connect':
                    timeout = jsn['params']['Timeout']
                    if timeout == 0:
                        timeout = 30

                    rt = cashreg_comlink.connect(jsn['params']['Host'], jsn['params']['Port'], timeout)
                    if rt != 0:
                        terminal.write(generateErrorJson(jsn['id']))
                        logging.error('Can not connect to host({})'.format(rt))
                        continue

                    terminal.write(generateSuccessJson(jsn['id']))

            elif method == 'Disconnect':
                cashreg_comlink.disconnect()
                terminal.write(generateSuccessJson(jsn['id']))

            elif method == 'SendData':
                timeout = jsn['params']['Timeout']
                if timeout == 0:
                    timeout = 30

                rc = cashreg_comlink.write(jsn['params']['Data'], timeout)

                if rc < 0:
                    terminal.write(generateErrorJson(jsn['id']))
                    logging.error('Failed to send data via ip on cashreg')
                    continue

                terminal.write(generateSuccessJson(jsn['id']))

            elif method == 'ReceiveData':
                timeout = jsn['params']['Timeout']
                if timeout == 0:
                    timeout = 30

                recvLen = int(jsn['params']['Bytes'])
                data = cashreg_comlink.read(recvLen, timeout)
                if len(data) == 0:
                    terminal.write(generateErrorJson(jsn['id']))
                    logging.error('Failed to receive data from ip on cash')
                    continue

                main = {}
                main['jsonrpc'] = '2.0'
                main['result'] = data
                main['id'] = jsn['id']

                json_data = json.dumps(main)
                terminal.write(json_data)

            elif method == "ContinueTransaction":
                global interruptState
                main = {}
                main['jsonrpc'] = '2.0'
                main['result'] = interruptState
                main['id'] = jsn['id']

                json_data = json.dumps(main)
                terminal.write(json_data)

        print('----------------------------')



