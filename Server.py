'''
Server module
14/04/21
Jesús A Bermúdez Silva
'''

import subprocess
import socket
import os
import net

SERVER_HOST = socket.gethostbyname(socket.gethostname())    # server IP address
SERVER_PORT = 65430                                         # Server well known port to listen on

def HandleRequests(reqRep):
    with reqRep:
        while True:
            data = reqRep.recvfrom(net.BUFFER_SIZE)
            if not data:
                break

            # inform appropriate translator of a new customer
            transType = str(data[0].decode())               # type of translator
            addrSpeaker = str(data[1][0])                   # speaker's address
            portSpeaker = str(data[1][1])                   # speaker's port
            print("Handled Request ", "Translator type: ", transType, "From address and port: ", addrSpeaker, portSpeaker)
            subprocess.Popen([os.getcwd() + "\\dist\\translator.exe", transType, addrSpeaker, portSpeaker])

print("Server IP : ", SERVER_HOST, "Server Port :", SERVER_PORT)
reqRep = net.getThisReqRepSocket((SERVER_HOST, SERVER_PORT))
HandleRequests(reqRep)



