'''
Babel Chat Speaker module

This is a client to the Babel Chat server.

Began on 14/04/21
Modified 31/05/21

Jesús A Bermúdez Silva
'''
import tkinter as tk
import socket
import select
import net
import threading
import os
import prot
from tkinter import messagebox

# constants
NO_USER = ""

LOCAL_HOST_IP_ADDR  = socket.gethostbyname(socket.gethostname())  # Local host IP address
SERVER              = ("192.168.1.189", 65430)
BABELCHAT_USER      = "00004"
BABELCHAT_CONTACT   = "Roger Dunn"
CONTACTS_FILE       = "Speaker3 Contacts"
MESSAGE_FILE        = "Speaker3 Messages"

SUB_WINDOWS_TITLE   = "Babel Chat   " + BABELCHAT_CONTACT

contacts = []  # list of list of contacts. Contains [contacts user id, user name, language spoken]

'''
list of lists that will contain messages buffered by the speaker for and from the different users
each list has format
user Id message to whom, user Id message from whom, message
'''
MSG_TO      = 0
MSG_FROM    = 1
MSG_DATA    = 2
messages    = []  # list of messages. Contains [user id of to whom, user id of from whom, message]

selectedUsers = []  # list of selected users. Contains [contacts user id]

'''
list to map available languages to google translate language codes and their position on the 
languages listbox
'''
languages = [
    ["English", "en", 0],
    ["French", "fr", 1],
    ["German", "de", 2],
    ["Italian", "it", 3],
    ["Spanish", "es", 4]
]

'''
======================================================================================
=======================  UTILITY functions ===========================================
======================================================================================
'''
'''
displays the contacts
'''
def DispContacts():
    for c in contacts:
        print(c)

'''
loads the contacts list from a configuration file
'''
def LoadContacts():
    if (os.path.isfile(CONTACTS_FILE)):
        with open(CONTACTS_FILE, "r") as contactsFile:
            for line in contactsFile:
                contact = line[:len(line) - 1].split(",")
                contacts.append(contact)
    else:
        messagebox.showwarning(SUB_WINDOWS_TITLE, "Loading Contacts - No contacts file")

'''
load messages from the message file
'''
def LoadMessages():
    if (os.path.isfile(MESSAGE_FILE)):
        with open(MESSAGE_FILE, "r") as msgFile:
            for line in msgFile:
                if line[len(line) - 1] == "\n":
                    line = line[:-1]
                msg = line.split(",", 2)  # split into from, to, msg. The message may have commas
                messages.append(msg)
    else:
        messagebox.showwarning(SUB_WINDOWS_TITLE, "Loading Messages. No messages file - new one created")

'''
Store all the messages into a file for permanent storage purposes
'''
def SaveMessages():
    with open(MESSAGE_FILE, "w") as msgFile:
        for m in messages:
            str = ",".join(m)
            str += "\n"
            msgFile.write(str)

'''
get a contact's user identifier from a contacts's name
'''
def GetUser(contact):
    for c in contacts:
        if contact == c[1]:
            return c[0]
    return NO_USER

'''
get a contact's name from a contact's user identifier
'''
def GetContact(user):
    for c in contacts:
        if user == c[0]:
            return c[1]
    return NO_USER

'''
changes display so that buffered mode communication is on
'''
def SetBufferedMode():
    global directComm

    directComm = False
    selectedUsers.clear()
    talkingTo.config(text="")
    inTray.config(state=tk.DISABLED)
    outTray.delete(0, tk.END)
    outTray.config(state=tk.NORMAL)
    callButton.configure(text="Call Contact")
    contactsLb.config(state=tk.NORMAL)
    contactsLb.selection_clear(0, tk.END)
    languageLb.config(state=tk.NORMAL)

'''
changes display so that direct communication mode is on
'''
def SetDirectCommMode():
    global directComm
    global directCaller

    directComm = True
    talkingTo.config(text=directCaller)
    inTray.config(state=tk.NORMAL)
    outTray.delete(0, tk.END)
    callButton.configure(text="Disconnect")
    contactsLb.config(state=tk.DISABLED)
    languageLb.config(state=tk.DISABLED)

'''
Send msg to server for buffering and append it to message queue for all selected users.
Then display in outTray.
'''
def BufferedDisplay(msg):
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
def DirectCommDisplay(msg):
    data = prot.TRANSLATE_CMD + "," + msg
    transSocket.send(data.encode())
    inTray.delete(0, len(msg))
    with outTrayLock:
        outTray.insert(0, "...")  # separating line between messages
        outTray.insert(0, msg)

'''
displays on the outTray the received message
'''
def DispReceivedMessage(msg):
    with outTrayLock:
        for u in selectedUsers:
            if msg[MSG_FROM] == u:
                outTray.insert(0, "...")  # separating line
                outTray.itemconfig(0, bg="#bdc1d6")
                outTray.itemconfig(0, foreground="black")
                contact = GetContact(u)
                contact = contact.split(" ")
                data = contact[0][0] + contact[1][0] + ": " + msg[MSG_DATA]
                outTray.insert(0, data)
                outTray.itemconfig(0, bg="#bdc1d6")
                outTray.itemconfig(0, foreground="black")

'''
displays on the outTray all messages
'''
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
                        contact = GetContact(u)
                        contact = contact.split(" ")
                        msg = contact[0][0] + contact[1][0] + ": " + data[MSG_DATA]
                        outTray.insert(0, msg)
                        outTray.itemconfig(0, bg="#bdc1d6")
                        outTray.itemconfig(0, foreground="black")
                    elif data[MSG_FROM] == BABELCHAT_USER and data[MSG_TO] == u:
                        outTray.insert(0, "...")  # separating line
                        outTray.insert(0, data[MSG_DATA])

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
loads the contacts list box from the contacts list
'''
def LoadContacs(lBox):
    index = 0
    for line in contacts:
        contact = line[1]
        lBox.insert(index, contact)
        lBox.itemconfig(index, bg="#bdc1d6")
        index += 1

'''
downloads messages from the server. Only used at start up time.
'''
def DownLoadMessages():
    DownLoadMessagesRequest()
    while True:
        fromServerSocket.settimeout(1.5)
        try:
            packet = fromServerSocket.recv(net.BUFFER_SIZE)
        except socket.timeout:
            messagebox.showerror(SUB_WINDOWS_TITLE, "Down Loading Messages: Unable to down load messages - No Server")
            exit(0)
        fromServerSocket.settimeout(None)
        m = packet.decode().split(",", 3)  # split into code, from, to, msg. The message may have commas
        if m[0] == prot.FINISH_DOWNLOAD:
            return
        if m[0] == prot.SENDING_MESSAGE:
            messages.append(m[1:])

'''
displays all downloaded messages, only used for debugging purposes
'''
def DispDownLoadedMessages():
    for m in messages:
        print(m)

'''
================================= END UTILITY FUNCTIONS =====================================
'''

''' 
============================== Functions to make requests to the server ==============================
'''

'''
Records on the server our stream IP address and port number
MESSAGE_TYPE, FROM_WHOM, STREAM_IP_ADDRESS, STREAM_PORT_NUMBER
'''
def RegisterUserRequest(reqRep, stream):
    data = prot.REGISTER_USER + "," + BABELCHAT_USER + "," + reqRep[0] + "," + str(reqRep[1]) + "," + stream[0] + "," + str(
        stream[1])
    toServerSocket.send(data.encode())

    fromServerSocket.settimeout(1.5)
    try:
        data = fromServerSocket.recv(net.BUFFER_SIZE)
    except socket.timeout:
        messagebox.showerror(SUB_WINDOWS_TITLE, "Registering Chat. Could not register chat - No server")
        exit(0)
    fromServerSocket.settimeout(None)
    data = data.decode()
    if data == prot.UNABLE_TO_REGISTER:
        messagebox.showerror(SUB_WINDOWS_TITLE, "Registering Chat. Could not register with server")
        exit(0)
    if data == prot.USER_REGISTERED:
        return

'''
tells server the user is no longer active
'''
def DeRegisterUserRequest():
    data = prot.DE_REGISTER_USER + "," + BABELCHAT_USER
    toServerSocket.send(data.encode())

'''
requests the given user's details from the server
'''
def GetUserRequest(user):
    data = prot.GET_USER + "," + BABELCHAT_USER + "," + user
    toServerSocket.send(data.encode())

'''
attempts a call to the given user
'''
def CallUserRequest(user):
    data = prot.CALL_USER + "," + BABELCHAT_USER + "," + user
    toServerSocket.send(data.encode())

'''
accepts/refuses a call request from a given user
'''
def AcceptCallRequest(user, accept):
    if accept:
        acceptCall = "TRUE"
    else:
        acceptCall = "FALSE"
    data = prot.ACCEPT_CALL_USER + "," + BABELCHAT_USER + "," + user + "," + acceptCall
    toServerSocket.send(data.encode())

'''
send message to buffer to server
'''
def BufferMessageRequest(user, msg):
    # MESSAGE_TYPE, FOR_WHOM, FROM_WHOM, DATA
    data = prot.BUFFER_MESSAGE + "," + user + "," + BABELCHAT_USER + "," + msg
    toServerSocket.send(data.encode())

'''
Down load messages from server
'''
def DownLoadMessagesRequest():
    data = prot.DOWNLOAD_MESSAGES + "," + BABELCHAT_USER
    toServerSocket.send(data.encode())

'''
get language user currently speaks
'''
def GetLanguageRequest():
    data = prot.GET_LANGUAGE + "," + BABELCHAT_USER
    toServerSocket.send(data.encode())
    packet = fromServerSocket.recv(net.BUFFER_SIZE)
    data = packet.decode().split(",")
    return data[1]

'''
set new language at server
'''
def SetLanguageRequest(code):
    data = prot.SET_LANGUAGE + "," + BABELCHAT_USER + "," + code
    toServerSocket.send(data.encode())

'''
request a translator
get translator socket to exchange with server
'''
def GetTranslatorRequest():
    global transSocket
    global directCaller

    transSocket = net.AnyReqRepSocket(LOCAL_HOST_IP_ADDR)
    myDetails = transSocket.getsockname()

    data = prot.GET_TRANSLATOR + "," + BABELCHAT_USER + "," + GetUser(directCaller) + "," + myDetails[0] + "," + str(myDetails[1])
    toServerSocket.send(data.encode())

    data = transSocket.recvfrom(net.BUFFER_SIZE)
    transLocation = (data[1][0], data[1][1])
    transSocket.connect(transLocation)

'''
============================ END OF FUNCTIONS THAT MAKE REQUESTS TO THE SERVER =====================
'''

'''
======================= Functions to handle input from the server ============================
==================== these run in a seperate thread ==========================================
================ The only shared resource is the message list. The code to access this =======
================ resource from this thread is protected by a lock ============================
'''

'''
Handle input from the server. 
'''
def handleServerInput(inSocket):
    while True:
        packet = inSocket.recv(net.BUFFER_SIZE)
        packet = packet.decode().split(",", 1)  # split into code, the rest
        if packet[0] == prot.SENDING_MESSAGE:  # received a user message?
            MessageArrived(packet[1])
        elif packet[0] == prot.USER_NOT_REG:  # received a user not registered
            messagebox.showinfo(SUB_WINDOWS_TITLE, "Direct Calling: " + GetContact(packet[1]) + " not available")
        elif packet[0] == prot.USER_CALLING:  # received a call request
            SomeoneCalling(packet[1])
        elif packet[0] == prot.USER_ACCEPTED_CALL:  # received an accept call
            AcceptCall(packet[1])
        elif packet[0] == prot.DE_REGISTERED_COMPLETE:
            return

'''
When a buffered message arrives store it in the message queue and display it on the outTray
'''
def MessageArrived(data):
    msg = data.split(",", 2)  # split into from, to, msg
    with messageLock:
        messages.append(msg)  # append it to messages list
    DispReceivedMessage(msg)  # shows message in outTray

'''
Some one has just called us. Reply to the request to call us depending on the user's
choice
'''
def SomeoneCalling(data):
    global directCaller

    directCaller = GetContact(data)
    msg = directCaller + " is calling. Accept Call?"
    acceptCall = messagebox.askyesno(SUB_WINDOWS_TITLE, "Direct Calling: " + msg)
    AcceptCallRequest(data, acceptCall)
    if acceptCall:
        directCallsThread = threading.Thread(target=HandleDirectCalls, args=(lSocket,), daemon=True)
        directCallsThread.start()  # handle direct calls

'''
Handle whether the contact one has attempted to call directly has accepted one's attempt or not.
If not give message and leave. Otherwise move to direct communication mode and connect directly 
using byte stream
'''
def AcceptCall(data):
    global peerSocket
    global directCaller

    data = data.split(",")
    directCaller = GetContact(data[0])
    if data[1] == "FALSE":
        messagebox.showinfo(SUB_WINDOWS_TITLE, "Direct Calling: " +  directCaller + " refused call")
        directCaller = ""
        return

    with peerLock:
        if peerSocket != None:
            peerSocket.close()
            peerSocket = None
        peerSocket = net.ConnectedStreamSocket((data[2], int(data[3])))
    GetTranslatorRequest()
    directCommThread = threading.Thread(target=HandleDirectComm, daemon=True)
    directCommThread.start()                # handle input from other in point to point mode

    SetDirectCommMode()

'''
======================== END of functions that handle input from the server thread ======================
'''

'''
accept communication request from the other end
this is a daemon thread, it dies by itself when program finished
'''
def HandleDirectCalls(lSocket):
        global peerSocket

#    while True:
        inputs = [lSocket]
        readable, _, _ = select.select(inputs, [], [])
        if readable:
            for s in readable:
                if s == lSocket:
                    with peerLock:
                        if peerSocket != None:
                            peerSocket.close()
                            peerSocket = None
                        peerSocket, _ = lSocket.accept()
                    GetTranslatorRequest()
                    directCommThread = threading.Thread(target=HandleDirectComm, daemon=True)
                    directCommThread.start()  # handle input from other in point to point mode
                    SetDirectCommMode()

'''
thread to handle the direct communication mode, where translator input is sent to peer,
and other peer input is displayed. 
'''
def HandleDirectComm():
    global peerSocket
    global transSocket

    while True:
        inputs = [peerSocket, transSocket]
        readable, _, _ = select.select(inputs, [], [])
        if readable:
            for s in readable:
                if s is peerSocket:
                    if not DoPeerSocket():
                        return
                elif s is transSocket:
                    data = transSocket.recv(net.BUFFER_SIZE)
                    peerSocket.send(data)

'''
handle the activity from the peerSocket
'''
def DoPeerSocket():
    global directCaller

    if peerSocket._closed:
        return False
    try:
        data = peerSocket.recv(net.BUFFER_SIZE)
    except ConnectionResetError:
        messagebox.showinfo(SUB_WINDOWS_TITLE, "Lost connection to " + directCaller)
        Disconnect()
        return False
    if not data:  # other end close connection?
        Disconnect()
        return False

    inTray.delete(0, tk.END)
    with outTrayLock:
        outTray.insert(0, "...")  # separating line
        outTray.insert(0, data.decode())
        outTray.itemconfig(0, bg="#bdc1d6")
        outTray.itemconfig(0, foreground="black")
    return True

'''
GUI event handlers. The possible events are call button pressed, change language
choose contact, in tray ready
'''

'''
button pressed to choose a contact to communicate with or finish direct call
'''
def CallButton():
    caption = callButton.cget("text")
    if caption == "Call Contact":
        CallContact()
    else:
        Disconnect()

'''
Call contact chosen
'''
def CallContact():
    if (len(selectedUsers) > 1):
        messagebox.showwarning(SUB_WINDOWS_TITLE, "Direct Calling: Can only connect to one contact at a time")
        return

    if (len(selectedUsers) == 0):
        messagebox.showwarning(SUB_WINDOWS_TITLE, "Direct Calling: Need to specify a contact")
        return

    # request from server contact's details
    CallUserRequest(selectedUsers[0])

'''
Disconnect a current active call.
'''
def Disconnect():
    global transSocket

    peerSocket.close()              # close peer connection
    data = prot.STOP_TRANSLATING_CMD
    transSocket.send(data.encode())  # stop translating thread
    transSocket.close()

    SetBufferedMode()               # change display mode to buffered mode

'''
the handling of any entered data depends on the mode we are on - direct communication 
or buffered 
'''
def inTrayReady(event):
    global directComm

    msg = inTray.get()
    if directComm:
        DirectCommDisplay(msg)
    else:
        BufferedDisplay(msg)

'''
selects from listbox all the selected contacts 
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
END OF GUI event handlers =============================================================
'''
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

callButton = tk.Button(win, text="Call Contact", command=CallButton)
messagePanel.create_window(320, 20, anchor=tk.NW, window=callButton)

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

enterLabel = tk.Label(win, text="Send message:")
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
lSocket = net.ListeningSocket(LOCAL_HOST_IP_ADDR)
streamDetails = lSocket.getsockname()

'''
sockets that will be defined later on
'''
transSocket = None
peerSocket = None

'''
We need two sockets to speak to the server. One for reading, the other for writing. 
We need two because the reading and writing are done via different threads and 
by having two sockets we avoid race conditions. 
'''
fromServerSocket = net.ConnectedReqRepSocket(LOCAL_HOST_IP_ADDR, SERVER)
toServerSocket = net.ConnectedReqRepSocket(LOCAL_HOST_IP_ADDR, SERVER)
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

'''
These are locks to ensure that 
'''
messageLock = threading.Lock()  # no simultaneous access to message list
outTrayLock = threading.Lock()  # no simultaneous access to outTray
peerLock    = threading.Lock()  # no simultaneous access to peerSocket

'''
handle network activity
'''
serverThread = threading.Thread(target=handleServerInput, args=(fromServerSocket,))
serverThread.start()  # handle input from the server

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

