'''
Network module

Utility functions for getting cooked sockets

14/04/21
Jesús A Bermúdez Silva
'''

import socket
BUFFER_SIZE = 1024              # maximum size buffer in UDP reads

'''
obtains a bound request reply socket to a particular port
'''
def ConnectedReqRepSocket(fromWhom, toWhom):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((fromWhom, 0))
    s.connect(toWhom)
    return s

'''
obtains a bound request reply socket to a particular port
'''
def ThisReqRepSocket(fromWhom):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind(fromWhom)
    return s

'''
obtains a bound request reply socket to any port
'''
def AnyReqRepSocket(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.bind((host,0))
    return s

'''
obtains a connected stream socket
'''
def ConnectedStreamSocket(toAddr):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(toAddr)
    return s

'''
obtains a socket used for listening to connections
'''
def ListeningSocket(host):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, 0))
    s.listen()
    return s

