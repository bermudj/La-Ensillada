'''
Network module
14/04/21
Jesús A Bermúdez Silva
'''


import socket
BUFFER_SIZE = 1024

# obtains a bound request reply socket to a particular port
def getConnectedReqRepSocket(host, toWhom):
    s = getAnyReqRepSocket(host)
    s.connect(toWhom)
    return s

# obtains a bound request reply socket to a particular port
def getThisReqRepSocket(fromWhom):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(fromWhom)
    return s

# obtains a bound request reply socket to any port
def getAnyReqRepSocket(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((host,0))
    return s

# obtains a connected stream socket
def getByteStreamSocket(toAddr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(toAddr)
    return s

#obtains a socket used for listening to connections
def getListeningSocket(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, 0))
    s.listen()
    return s

