'''
Server module
14/04/21
Jesús A Bermúdez Silva
'''
import os
import socket
import net
import threading
from googletrans import Translator

# Request Codes
REGISTER_USER       = "1"
DE_REGISTER_USER    = "2"
GET_USER            = "3"
CALL_USER           = "4"
GET_TRANSLATOR      = "5"
BUFFER_MESSAGE      = "6"
DOWNLOAD_MESSAGES   = "7"
SET_LANGUAGE        = "8"
GET_LANGUAGE        = "9"
ACCEPT_CALL_USER    = "10"

# Reply Codes
USER_REGISTERED     = "0"
UNABLE_TO_REGISTER  = "1"
USER_NOT_REG        = "2"
USER_IS             = "3"
FINISH_DOWNLOAD     = "4"
FINISHED_RUNNING    = "5"
SENDING_MESSAGE     = "6"
LANGUAGE_USED       = "7"
USER_CALLING        = "8"
USER_ACCEPTED_CALL  = "9"

# Request Codes to translator
TRANSLATE_CMD           = "0"
STOP_TRANSLATING_CMD    = "1"

# Constants
NO_LANG         = "0"
USER_OFF        = "OFF"
USER_ON         = "ON"

# list of lists that will contain all users of the Comms box system
# each list has format
# user id, active, user name, language, ReqRep Address, Stream Address
USER_ID         = 0
USER_NAME       = 1
USER_LANGUAGE   = 2
USER_ACTIVE     = 3
USER_REQREP_IP  = 4
USER_REQREP_PORT= 5
USER_STREAM_IP  = 6
USER_STREAM_PORT= 7
REGISTER_FIELD  = 4


users = []

#list of lists that will contain messages buffered by the server for different users
# each list has format
#user Id message to whom, user Id message from whom, message
MSG_TO      = 0
MSG_FROM    = 1
MSG_DATA    = 2
messages    = []    # list of messages. Contains [user id of to whom, user id of from whom, message]

SERVER_HOST = socket.gethostbyname(socket.gethostname())    # server IP address
SERVER_PORT = 65430                                         # Server well known port to listen on

USERS_FILE = "users"

# displays the users for logging purposes
def DispUsers():
    for u in users:
        print(u)

# loads the users list from a configuration file
def LoadUsers():
    if (os.path.isfile(USERS_FILE)):
        with open(USERS_FILE, "r") as usersFile:
            for line in usersFile:
                user = line[:len(line) - 1].split(",")
                user.insert(USER_ACTIVE, USER_OFF)
                users.append(user)
    else:
        print("Error no users file")

# Saves all the users to a file
def SaveUsers():
    with open(USERS_FILE, "w") as userFile:
        for u in users:
            str = ",".join(u[0:USER_ACTIVE])
            str += "\n"
            userFile.write(str)

'''
records that the user is currently active.
It also registers the IP address and port number of the user
'''
def RegisterUserAsOn(data):
    data = data.split(",")
    registered = False
    index = 0
    for u in users:
        if u[USER_ID] == data[0]:    # found user?
            if len(users[index]) > REGISTER_FIELD:              # already registered location
                users[index] = users[index][0:REGISTER_FIELD]   # remove registered location

            users[index][USER_ACTIVE] = USER_ON

            # register IP and Ports
            users[index].append(data[1])    # IP address for ReqRep socket
            users[index].append(data[2])    # Port number for ReqRep socket
            users[index].append(data[3])    # IP address for stream socket
            users[index].append(data[4])    # Port number for stream socket

            registered = True
            break
        index += 1

    if registered:
        code = USER_REGISTERED
    else:
        code = UNABLE_TO_REGISTER
    reqRep.sendto(code.encode(), (data[1], int(data[2])))
    print("Message sent ", code)


# records that the user is no longer active.
# It removes registered IP addresses and port numbers of the user
def DeRegisterUserAsOn(user):
    index = 0
    for u in users:
        if u[USER_ID] == user:    # found user?
            users[index] = users[index][0:REGISTER_FIELD]   # remove registered location
            users[index][USER_ACTIVE] = USER_OFF
            break
        index += 1

# gets a registered user
def GetRegUser(user):
    for u in users:
        if u[USER_ID] == user and u[USER_ACTIVE] == USER_ON:  # found user?
            return u
    return USER_NOT_REG

# get the user language
def GetLang(user):
    for u in users:
        if u[USER_ID] == user:                 # found user?
            return u[USER_LANGUAGE]
    return NO_LANG

# returns the speaker's request reply address
def GetReqRepAddr(user):
    u = GetRegUser(user)
    if u == USER_NOT_REG:
        return (USER_NOT_REG, int(USER_NOT_REG))
    return (u[USER_REQREP_IP], int(u[USER_REQREP_PORT]))

# display message list
def DispMessages():
    for m in messages:
        print(m)

# store message on message list
def BufferMessage(message):
    messages.append(message)

# download messages for user only if user is currently active
def DownLoadMessages(user):
    for u in users:
        if u[USER_ACTIVE] == USER_ON and u[USER_ID] == user:
            DownLoadMessagesActiveUser(u[USER_ID])

# send buffered messages for user. It assumes user is active
def DownLoadMessagesActiveUser(user):

    speakerAddr = GetReqRepAddr(user)

    translator = Translator()
    toLang = GetLang(user)

    j = 0
    l = len(messages)
    while j < l:
        m = messages[j].split(",", 2)
        if m[MSG_TO] == user:
            fromLang = GetLang(m[MSG_FROM])
            msg = translator.translate(m[MSG_DATA], src=fromLang, dest=toLang)
            data = SENDING_MESSAGE + "," + m[MSG_TO] + "," + m[MSG_FROM] + "," + msg.text
            reqRep.sendto(data.encode(), speakerAddr)
            print("Message Sent ", data)
            messages.pop(j)
            l -= 1
        else:
            j += 1

    data = FINISH_DOWNLOAD
    reqRep.sendto(data.encode(), speakerAddr)
    print("Message Sent ", data)

'''
Functions to handle the different requests to the server =========================
'''
# handle a register user request
def RegisterUserRequest(requestInfo):
    RegisterUserAsOn(requestInfo)
    DispUsers()

# handle a de-register user request
def DeRegisterUserRequest(requestInfo):
    speakerAddr = GetReqRepAddr(requestInfo)
    DeRegisterUserAsOn(requestInfo)
    data = FINISHED_RUNNING
    reqRep.sendto(data.encode(), speakerAddr)
    print("Message sent ", data)
    DispUsers()

# get a user and its stream details
def GetUserRequest(requestInfo):
    data = requestInfo.split(",")
    addr = GetReqRepAddr(data[0])
    user = GetRegUser(data[1])
    if user == USER_NOT_REG:
        data = USER_NOT_REG + "," + data[1]
    else:
        data = USER_IS + "," + data[1] + "," + user[USER_STREAM_IP] + "," + user[USER_STREAM_PORT]

    reqRep.sendto(data.encode(), addr)
    print("Message Sent ", data)


# informs a user another user was to make a direct call, from - data[0], to data[1]
def CallUserRequest(requestInfo):
    data = requestInfo.split(",")
    user = GetRegUser(data[1])
    if user == USER_NOT_REG:
        msg = USER_NOT_REG + "," + data[1]
        addr = GetReqRepAddr(data[0])
    else:
        msg = USER_CALLING + "," + data[0]
        addr = GetReqRepAddr(data[1])

    reqRep.sendto(msg.encode(), addr)
    print("Message Sent ", msg)

'''
informs caller whether its attempt to make a direct call failed/succeeded
data[0] - who is accepting/rejecting, data[1] - from whom it is accepting/rejecting
data[2] - accept/reject
'''
def AcceptCallUserRequest(requestInfo):
    data = requestInfo.split(",")
    user = GetRegUser(data[1])
    if user == USER_NOT_REG:
        msg = USER_NOT_REG + "," + data[1]
        addr = GetReqRepAddr(data[0])
    else:
        myDetails = GetRegUser(data[0])
        msg = USER_ACCEPTED_CALL + "," + data[0] + "," + data[2] + "," + myDetails[USER_STREAM_IP] + "," + myDetails[USER_STREAM_PORT]
        addr = GetReqRepAddr(data[1])

    reqRep.sendto(msg.encode(), addr)
    print("Message Sent ", msg)

# upon receiving a message from the speaker, place it into the message list and
# downloaded it to the speakers if they are available
def BufferMessageRequest(requestInfo):
    BufferMessage(requestInfo)
    requestInfo = requestInfo.split(",")
    DownLoadMessages(requestInfo[0])

# changes language for user
def SetLanguageRequest(requestInfo):
    requestInfo = requestInfo.split(",")
    for u in users:
        if u[USER_ID] == requestInfo[0]:                 # found user?
            u[USER_LANGUAGE] = requestInfo[1]
    SaveUsers()

# gets the current user language and sends it to the user
def GetLanguageRequest(requestInfo):
    requestInfo = requestInfo.split(",")
    speakerAddr = GetReqRepAddr(requestInfo[0])
    language = GetLang(requestInfo[0])
    data = LANGUAGE_USED + "," + language
    reqRep.sendto(data.encode(), speakerAddr)
    print("Message Sent ", data)

def GetTranslatorRequest(requestInfo):
    data = requestInfo.split(",")
    srcLang = GetLang(data[0])      # source language
    dstLang = GetLang(data[1])      # dst language
    addrSpeaker = data[2]           # speaker's address
    portSpeaker = data[3]           # speaker's port
    transThread = threading.Thread(target=translate, args=(srcLang, dstLang, addrSpeaker, portSpeaker,))
    transThread.start()

'''
Thread to translate when the operation is peer to peer
'''
def translate(srcLang, dstLang, addrSpeaker, portSpeaker):
    spkSocket = net.getConnectedReqRepSocket(SERVER_HOST, (addrSpeaker, int(portSpeaker)))
    spkSocket.send(b"Translator's whereabouts ")
    translator = Translator()

    while True:
        word = spkSocket.recv(net.BUFFER_SIZE)
        word = word.decode().split(",")
        if word[0] == STOP_TRANSLATING_CMD:             # stop translating thread?
            return
        result = translator.translate(word[1], src=srcLang, dest=dstLang)
        spkSocket.send(result.text.encode())

# handle requests to the server from the speaker
def HandleRequests(reqRep):
    with reqRep:
        while True:
            packet = reqRep.recvfrom(net.BUFFER_SIZE)
            if not packet:
                break

            data = packet[0].decode().split(",", 1) # the data part of the packet
            addr = packet[1]                        # the source address of the packet

            speakerRequest = data[0]               # request from speaker
            requestInfo = data[1]                  # info associated with request
            print("Request received", data, addr)

            if speakerRequest == REGISTER_USER:
                RegisterUserRequest(requestInfo)
            elif speakerRequest == GET_USER:
                GetUserRequest(requestInfo)
            elif speakerRequest == CALL_USER:
                CallUserRequest(requestInfo)
            elif speakerRequest == ACCEPT_CALL_USER:
                AcceptCallUserRequest(requestInfo)
            elif speakerRequest == GET_TRANSLATOR:
                GetTranslatorRequest(requestInfo)
            elif speakerRequest == BUFFER_MESSAGE:
                BufferMessageRequest(requestInfo)
            elif speakerRequest == DOWNLOAD_MESSAGES:
                DownLoadMessages(requestInfo)
            elif speakerRequest == DE_REGISTER_USER:
                DeRegisterUserRequest(requestInfo)
            elif speakerRequest == SET_LANGUAGE:
                SetLanguageRequest(requestInfo)
            elif speakerRequest == GET_LANGUAGE:
                GetLanguageRequest(requestInfo)

LoadUsers()

print("Server IP : ", SERVER_HOST, "Server Port :", SERVER_PORT)
reqRep = net.getThisReqRepSocket((SERVER_HOST, SERVER_PORT))
HandleRequests(reqRep)

'''

from google.cloud import translate_v2 as translate

translate_client = translate.Client()

if isinstance(text, six.binary_type):
    text = text.decode("utf-8")

# Text can also be a sequence of strings, in which case this method
# will return a sequence of results for each text.
result = translate_client.translate(text, target_language=target)

return result["translatedText"]

'''


