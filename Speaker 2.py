'''
Speaker module
14/04/21
Jesús A Bermúdez Silva
'''
import tkinter as tk
import socket
import select
import net
import threading
import os
from tkinter import messagebox

# Request Codes
REGISTER_USER = "1"
DE_REGISTER_USER = "2"
GET_USER = "3"
CALL_USER = "4"
GET_TRANSLATOR = "5"
BUFFER_MESSAGE = "6"
DOWNLOAD_MESSAGES = "7"
SET_LANGUAGE = "8"
GET_LANGUAGE = "9"
ACCEPT_CALL_USER = "10"

# Reply Codes
USER_REGISTERED = "0"
UNABLE_TO_REGISTER = "1"
USER_NOT_REG = "2"
USER_IS = "3"
FINISH_DOWNLOAD = "4"
FINISHED_RUNNING = "5"
SENDING_MESSAGE = "6"
LANGUAGE_USED = "7"
USER_CALLING = "8"
USER_ACCEPTED_CALL = "9"

# constants
NO_USER = ""

LOCAL_HOST_IP_ADDR = socket.gethostbyname(socket.gethostname())  # Local host IP address
SERVER = ("192.168.1.189", 65430)
BABELCHAT_USER = "00001"
BABELCHAT_CONTACT = "Rich"
CONTACTS_FILE = "Speaker2 Contacts"
MESSAGE_FILE = "Speaker2 Messages"

contacts = []  # list of list of contacts. Contains [contacts user id, user name, language spoken]

# list of lists that will contain messages buffered by the speaker for and from the different users
# each list has format
# user Id message to whom, user Id message from whom, message
MSG_TO = 0
MSG_FROM = 1
MSG_DATA = 2
messages = []  # list of messages. Contains [user id of to whom, user id of from whom, message]

selectedUsers = []  # list of selected users. Contains [contacts user id]

# list to map available languages to google translate language codes and their position on the listbox
languages = [
    ["English", "en", 0],
    ["French", "fr", 1],
    ["German", "de", 2],
    ["Italian", "it", 3],
    ["Spanish", "es", 4]
]

# displays the contacts
def DispContacts():
    for c in contacts:
        print(c)

# loads the contacts list from a configuration file
def LoadContacts():
    if (os.path.isfile(CONTACTS_FILE)):
        with open(CONTACTS_FILE, "r") as contactsFile:
            for line in contactsFile:
                contact = line[:len(line) - 1].split(",")
                contacts.append(contact)
    else:
        messagebox.showwarning("Loading Contacts", "No contacts file")

# load messages from the message file
def LoadMessages():
    if (os.path.isfile(MESSAGE_FILE)):
        with open(MESSAGE_FILE, "r") as msgFile:
            for line in msgFile:
                if line[len(line) - 1] == "\n":
                    line = line[:-1]
                msg = line.split(",", 2)  # split into from, to, msg. The message may have commas
                messages.append(msg)
    else:
        messagebox.showwarning("Loading Messages", "No messages file - new one created")

# Store all the messages into a file
def SaveMessages():
    with open(MESSAGE_FILE, "w") as msgFile:
        for m in messages:
            str = ",".join(m)
            str += "\n"
            msgFile.write(str)

# get a contact's user identifier from a contacts's name
def GetUser(contact):
    for c in contacts:
        if contact == c[1]:
            return c[0]
    return NO_USER

# get a contact's name from a contact's user identifier
def GetContact(user):
    for c in contacts:
        if user == c[0]:
            return c[1]
    return NO_USER

''' Functions to make requests to the server
record on the server our stream IP address and port number
MESSAGE_TYPE, FROM_WHOM, STREAM_IP_ADDRESS, STREAM_PORT_NUMBER
'''
def RegisterUserRequest(reqRep, stream):
    data = REGISTER_USER + "," + BABELCHAT_USER + "," + reqRep[0] + "," + str(reqRep[1]) + "," + stream[0] + "," + str(
        stream[1])
    toServerSocket.send(data.encode())

    fromServerSocket.settimeout(1.5)
    try:
        data = fromServerSocket.recv(net.BUFFER_SIZE)
    except socket.timeout:
        messagebox.showerror("Registering Chat", "Could not register chat - No server")
        exit(0)
    fromServerSocket.settimeout(None)
    data = data.decode()
    if data == UNABLE_TO_REGISTER:
        messagebox.showerror("Registering Chat", "Could not register chat")
        exit(0)
    if data == USER_REGISTERED:
        return

# tells server the user is no longer active
def DeRegisterUserRequest():
    data = DE_REGISTER_USER + "," + BABELCHAT_USER
    toServerSocket.send(data.encode())

# requests the given user's details from the server
def GetUserRequest(user):
    data = GET_USER + "," + BABELCHAT_USER + "," + user
    toServerSocket.send(data.encode())

# attempts a call to the given user
def CallUserRequest(user):
    data = CALL_USER + "," + BABELCHAT_USER + "," + user
    toServerSocket.send(data.encode())

# accepts/refuses a call request from a given user
def AcceptCallRequest(user, accept):
    if accept:
        acceptCall = "TRUE"
    else:
        acceptCall = "FALSE"
    data = ACCEPT_CALL_USER + "," + BABELCHAT_USER + "," + user + "," + acceptCall
    toServerSocket.send(data.encode())

# send message to buffer to server
def BufferMessageRequest(user, msg):
    # MESSAGE_TYPE, FOR_WHOM, FROM_WHOM, DATA
    data = BUFFER_MESSAGE + "," + user + "," + BABELCHAT_USER + "," + msg
    toServerSocket.send(data.encode())

# Down load messages from server
def DownLoadRequest():
    data = DOWNLOAD_MESSAGES + "," + BABELCHAT_USER
    toServerSocket.send(data.encode())

# get language user currently speaks
def GetLanguageRequest():
    data = GET_LANGUAGE + "," + BABELCHAT_USER
    toServerSocket.send(data.encode())
    packet = fromServerSocket.recv(net.BUFFER_SIZE)
    data = packet.decode().split(",")
    return data[1]

# set new language at server
def SetLanguageRequest(code):
    data = SET_LANGUAGE + "," + BABELCHAT_USER + "," + code
    toServerSocket.send(data.encode())

# request a translator
# get translator socket to exchange with server
def GetTranslatorRequest():
    global directCaller
    global transSocket

    transSocket = net.getAnyReqRepSocket(LOCAL_HOST_IP_ADDR)
    myDetails = transSocket.getsockname()

    callingUser = GetUser(directCaller)
    data = GET_TRANSLATOR + "," + BABELCHAT_USER + "," + callingUser + "," + myDetails[0] + "," + str(myDetails[1])
    toServerSocket.send(data.encode())

    data = transSocket.recvfrom(net.BUFFER_SIZE)
    transLocation = (data[1][0], data[1][1])
    transSocket.connect(transLocation)

'''
Handle input/output from the network. This runs as a separate thread from the main program thread.
The only shared resource is the message list. The code to access this resource from this thread
is protected by a lock
'''
def handleServerInput(inSocket):
    while True:
        packet = inSocket.recv(net.BUFFER_SIZE)
        packet = packet.decode().split(",", 1)  # split into code, the rest
        if packet[0] == SENDING_MESSAGE:  # received a user message?
            MessageArrived(packet[1])
        elif packet[0] == USER_NOT_REG:  # received a user not registered
            messagebox.showinfo("User Not Active", GetContact(packet[1]))
        elif packet[0] == USER_CALLING:  # received a call request
            SomeoneCalling(packet[1])
        elif packet[0] == USER_ACCEPTED_CALL:  # received an accept call
            AcceptCall(packet[1])
        elif packet[0] == FINISHED_RUNNING:
            return

# when a buffered message arrives store it in the message queue and display it on the outTray
def MessageArrived(data):
    msg = data.split(",", 2)  # split into from, to, msg
    with messageLock:
        messages.append(msg)  # append it to messages list
    DispReceivedMessage(msg)  # shows message in outTray


def SomeoneCalling(data):
    global directCaller

    directCaller = GetContact(data)
    msg = directCaller + " is calling"
    acceptCall = messagebox.askyesno(msg, "Accept Call?")
    AcceptCallRequest(data, acceptCall)


def SetDirectCommMode():
    global directComm

    directComm = True
    talkingTo.config(text=directCaller)
    inTray.config(state=tk.NORMAL)
    connectButton.configure(text="disconnect")
    contactsLb.config(state=tk.DISABLED)
    languageLb.config(state=tk.DISABLED)

'''
Handle whether the contact one has attempted to call directly has accepted one's attempt or not.
If not give message and leave. Otherwise move to direct communication mode and connect directly 
using byte stream
'''
def AcceptCall(data):
    global streamOther
    global directCaller

    data = data.split(",")
    directCaller = GetContact(data[0])
    if data[1] == "TRUE":
        msg = directCaller + " accepted call"
        messagebox.showinfo("accept call", msg)
    else:
        msg = directCaller + " refused call"
        messagebox.showinfo("accept call", msg)
        return

    streamOther = net.getByteStreamSocket((data[2], int(data[3])))
    GetTranslatorRequest()
    directCommThread = threading.Thread(target=HandleDirectComm)
    directCommThread.start()  # handle input from other in point to point mode

    SetDirectCommMode()

# accept communication request from the other end
# this is a thread
# need to kill this thread at end
def HandleDirectCalls(lSocket):
    global streamOther

    while True:
        streamOther, _ = lSocket.accept()

        GetTranslatorRequest()
        directCommThread = threading.Thread(target=HandleDirectComm)
        directCommThread.start()  # handle input from other in point to point mode

        SetDirectCommMode()


'''
# accept communication request from the other end
# this is a thread
'''
def HandleDirectComm():
    global directComm
    global directCaller
    global streamOther
    global transSocket

    while True:
        inputs = [streamOther, transSocket]
        readable, _, _ = select.select(inputs, [], [])
        if readable:
            for s in readable:
                if s is streamOther:
                    data = streamOther.recv(net.BUFFER_SIZE)
                    inTray.delete(0, tk.END)
                    with outTrayLock:
                        outTray.insert(0, "...")  # separating line
                        outTray.insert(0, data.decode())
                        outTray.itemconfig(0, bg="#bdc1d6")
                        outTray.itemconfig(0, foreground="black")
                if s is transSocket:
                    data = transSocket.recv(net.BUFFER_SIZE)
                    streamOther.send(data)

# once we choose a contact to communicate with
def callContacts():
    if (len(selectedUsers) > 1):
        messagebox.showwarning("Direct Call to Contact", "Can only connect to one contact at a time")
        return

    if (len(selectedUsers) == 0):
        messagebox.showwarning("Direct Call to Contact", "Need to specify a contact")
        return

    # request from server contact's details
    CallUserRequest(selectedUsers[0])

'''
Send msg to server for buffering and append it to message queue for all selected users.
Then display in outTray.
'''
def BufferedDisplay():
    msg = inTray.get()

    for user in selectedUsers:
        BufferMessageRequest(user, msg)
        with messageLock:
            messages.append([user, BABELCHAT_USER, msg])

    inTray.delete(0, len(msg))
    with outTrayLock:
        outTray.insert(0, "...")  # separating line between messages
        outTray.insert(0, msg)

'''
send message directly to other user, then display it
'''
def DirectCommDisplay():
    msg = inTray.get()
    transSocket.send(msg.encode())
    inTray.delete(0, len(msg))
    with outTrayLock:
        outTray.insert(0, "...")  # separating line between messages
        outTray.insert(0, msg)

'''
the handling of any entered data depends on the mode we are on - direct communication 
or buffered 
'''


def inTrayReady(event):
    global transSocket
    global directComm

    if directComm:
        DirectCommDisplay()
    else:
        BufferedDisplay()


# loads the contacts list box from the contacts list
def LoadContacs(lBox):
    index = 0
    for line in contacts:
        contact = line[1]
        lBox.insert(index, contact)
        lBox.itemconfig(index, bg="#bdc1d6")
        index += 1


# displays on the outTray the received message
def DispReceivedMessage(msg):
    with outTrayLock:
        for u in selectedUsers:
            if msg[MSG_FROM] == u:
                outTray.insert(0, "...")  # separating line
                outTray.itemconfig(0, bg="#bdc1d6")
                outTray.itemconfig(0, foreground="black")
                data = GetContact(u) + ": " + msg[MSG_DATA]
                outTray.insert(0, data)
                outTray.itemconfig(0, bg="#bdc1d6")
                outTray.itemconfig(0, foreground="black")


# displays on the outTray all messages
def DispMessages():
    with outTrayLock:
        outTray.delete(0, tk.END)
        with messageLock:
            for data in messages:
                for u in selectedUsers:
                    if data[MSG_FROM] == u:
                        outTray.insert(0, "...")  # separating line
                        outTray.itemconfig(0, bg="#bdc1d6")
                        outTray.itemconfig(0, foreground="black")
                        msg = GetContact(u) + ": " + data[MSG_DATA]
                        outTray.insert(0, msg)
                        outTray.itemconfig(0, bg="#bdc1d6")
                        outTray.itemconfig(0, foreground="black")
                    elif data[MSG_FROM] == BABELCHAT_USER and data[MSG_TO] == u:
                        outTray.insert(0, "...")  # separating line
                        outTray.insert(0, data[MSG_DATA])


# displays all downloaded messages, only used for debugging purposes
def DispDownLoadedMessages():
    for m in messages:
        print(m)


'''
downloads messages from the server. Only used at start up time.
'''


def DownLoadMessages():
    DownLoadRequest()
    while True:
        fromServerSocket.settimeout(1.5)
        try:
            packet = fromServerSocket.recv(net.BUFFER_SIZE)
        except socket.timeout:
            messagebox.showerror("Down Loading Messages", "Unable to down load messages - No Server")
            exit(0)
        fromServerSocket.settimeout(None)
        m = packet.decode().split(",", 3)  # split into code, from, to, msg. The message may have commas
        if m[0] == FINISH_DOWNLOAD:
            return
        if m[0] == SENDING_MESSAGE:
            messages.append(m[1:])


'''
upon select contacts button selects from listbox all the selected contacts 
places them in the selectedContacts list and displays contacts on the message panel
'''


def SelectContacts(event):
    users = ""
    selectedUsers.clear()
    cUser = contactsLb.curselection()
    first = True
    for i in cUser:
        user = contactsLb.get(i)
        selectedUsers.append(GetUser(user))
        if first:
            users = users + user
            first = False
        else:
            users = users + ", " + user

    if users != "":
        talkingTo.config(text=users)
        inTray.config(state=tk.NORMAL)
    else:
        talkingTo.config(text=users)
        inTray.config(state=tk.DISABLED)

    DispMessages()


'''
chooses language from available language in language list box and sets new
language on server
'''


def SelectLanguage(event):
    language = languageLb.get(tk.ACTIVE)

    code = "es"  # default setting if language cannot be found
    for l in languages:
        if l[0] == language:
            code = l[1]
            break

    SetLanguageRequest(code)


'''
loads the languages list box and chooses current language
'''


def LoadLanguages(lBox):
    for l in languages:
        lBox.insert(l[2], l[0])

    language = GetLanguageRequest()  # get language speaker currently uses

    index = 0  # default index
    for l in languages:
        if l[1] == language:
            index = l[2]

    lBox.see(index)
    lBox.activate(index)


'''
create user interface. It consists of two panels, each being a canvas widget. The contacts panel
holds a contacts listbox and language listbox. The message panel holds an entry widget to enter a message
and a listbox to hold sent messages.
'''
win = tk.Tk()
win.geometry('700x300')
win.config(bg='#446644')
win.wm_title("Babel Chat                            " + BABELCHAT_CONTACT)

'''
contact panel
'''
contactPanel = tk.Canvas(win, height=280, width=200)
contactPanel.grid(row=0, column=0, padx=5, pady=5)

headLabel = tk.Label(win, text="Contacts")
contactPanel.create_window(50, 10, anchor=tk.NW, window=headLabel)

contactsLb = tk.Listbox(win, selectmode="multiple", exportselection=0)
contactsLb.bind('<<ListboxSelect>>', SelectContacts)
contactPanel.create_window(10, 40, anchor=tk.NW, width=140, height=160, window=contactsLb)

contactsSb = tk.Scrollbar(win, orient=tk.VERTICAL)
contactsLb.configure(yscrollcommand=contactsSb.set)
contactsSb.config(command=contactsLb.yview)
contactPanel.create_window(150, 40, anchor=tk.NW, height=160, window=contactsSb)

headLabel = tk.Label(win, text="Language")
contactPanel.create_window(50, 210, anchor=tk.NW, window=headLabel)

languageLb = tk.Listbox(win, selectmode='single', exportselection=0)
contactPanel.create_window(10, 240, anchor=tk.NW, height=20, window=languageLb)
languageLb.bind('<<ListboxSelect>>', SelectLanguage)

'''
message panel
'''
messagePanel = tk.Canvas(win, height=280, width=480)
messagePanel.grid(row=0, column=1)

talkingTo = tk.Label(win, text="      ")
messagePanel.create_window(40, 15, anchor=tk.NW, window=talkingTo)

connectButton = tk.Button(win, text="Call Contact", command=callContacts)
messagePanel.create_window(320, 20, anchor=tk.NW, window=connectButton)

outTray = tk.Listbox(win, exportselection=0)
messagePanel.create_window(10, 50, anchor=tk.NW, width=400, height=150, window=outTray)

outTrayVSb = tk.Scrollbar(win, orient=tk.VERTICAL)
outTray.configure(yscrollcommand=outTrayVSb.set)
outTrayVSb.config(command=outTray.yview)
messagePanel.create_window(410, 50, anchor=tk.NW, height=150, window=outTrayVSb)

outTrayHSb = tk.Scrollbar(win, orient=tk.HORIZONTAL)
outTray.configure(xscrollcommand=outTrayHSb.set)
outTrayHSb.config(command=outTray.xview)
messagePanel.create_window(10, 200, anchor=tk.NW, width=400, window=outTrayHSb)

enterLabel = tk.Label(win, text="Send a message:")
messagePanel.create_window(10, 220, anchor=tk.NW, window=enterLabel)

inTray = tk.Entry(win)
messagePanel.create_window(10, 240, anchor=tk.NW, width=300, window=inTray)
inTray.bind("<Return>", inTrayReady)
inTray.config(state=tk.DISABLED)

'''
load contacts from contacts file
'''
LoadContacts()

'''
load messages from messages file
'''
LoadMessages()

'''
keeps track of mode of communication. Whether communicating one to one, or buffered via the server
'''
directComm = False

'''
get a listening socket so that we can communicate one to one
'''
lSocket = net.getListeningSocket(LOCAL_HOST_IP_ADDR)
streamDetails = lSocket.getsockname()

'''
We need two sockets to speak to the server. One for reading, the other for writing. 
We need two because the reading and writing are done via different threads and 
by having two sockets we avoid race conditions. 
'''
fromServerSocket = net.getConnectedReqRepSocket(LOCAL_HOST_IP_ADDR, SERVER)
toServerSocket = net.getConnectedReqRepSocket(LOCAL_HOST_IP_ADDR, SERVER)
reqRepDetails = fromServerSocket.getsockname()

'''
tell server the speaker is on
'''
RegisterUserRequest(reqRepDetails, streamDetails)

'''
get any buffered messages from server
'''
DownLoadMessages()

'''
load listboxes
'''
LoadContacs(contactsLb)
LoadLanguages(languageLb)

transSocket = 0

messageLock = threading.Lock()  # lock to ensure no simultaneous access to message list
outTrayLock = threading.Lock()  # lock to ensure no simultaneous access to outTray

'''
handle network activity
'''
serverThread = threading.Thread(target=handleServerInput, args=(fromServerSocket,))
serverThread.start()  # handle input from the server

directCallsThread = threading.Thread(target=HandleDirectCalls, args=(lSocket,))
directCallsThread.start()  # handle direct calls

'''
handle input from the user
'''
win.mainloop()

'''
tell server we have finished
'''
DeRegisterUserRequest()

'''
save all messages on a file for permanent storage
'''
SaveMessages()

exit()

'''    



    # request a translator
    # get translator socket to exchange with server
    transSocket = net.getAnyReqRepSocket(LOCAL_HOST_IP_ADDR)
    myDetails = transSocket.getsockname()

    data = GET_TRANSLATOR + "," + BABELCHAT_USER + "," + user + "," + myDetails[0] + "," + str(myDetails[1])
    toServerSocket.send(data.encode())

    data = transSocket.recvfrom(net.BUFFER_SIZE)
    transLocation = (data[1][0], data[1][1])
    transSocket.connect(transLocation)

    # netThread = threading.Thread(target=handleNet, args=(transSocket, streamOther, outTray))
    # netThread.start()


    connectButton.configure(text="disconnect")
'''
