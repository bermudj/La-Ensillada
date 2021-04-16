'''
Speaker module
14/04/21
Jesús A Bermúdez Silva
'''
import socket
import msvcrt
import select
import net

ENGLISH_SPANISH = "1"

LOCAL_HOST  = socket.gethostbyname(socket.gethostname()) # Local host IP address

SERVER_HOST = input("Enter server IP address: ")
SERVER_PORT = int(input("Enter server port: "))

# get request reply socket to obtain a translator
transSocket = net.getAnyReqRepSocket(LOCAL_HOST)

#   request translator
data = ENGLISH_SPANISH
transSocket.sendto(data.encode(), (SERVER_HOST, SERVER_PORT))

#   get translator's location
data = transSocket.recvfrom(net.BUFFER_SIZE)
transLocation = (data[1][0], data[1][1])
transSocket.connect(transLocation)

# my details
lSocket = net.getListeningSocket(LOCAL_HOST)
myDetails = lSocket.getsockname()
print("My details are: ", myDetails)

# get other speaker
print("Enter other's details or wait for the other to connect")

done = False
while not done:
    if msvcrt.kbhit():
        addrOther = input("Address : ")
        portOther = input("Port: ")
        streamOther = net.getByteStreamSocket((addrOther, int(portOther)))
        done = True
    else:
        inputs = [lSocket]
        readable, _, _ = select.select(inputs, [], [], 0)
        if readable:
            streamOther, _ = lSocket.accept()
            done = True

# Now we are connected to the other speaker as well as the translator.
# We can then exchange messages with the other after having been translated
print("connected")
done = False
while not done:
    if msvcrt.kbhit():
        # get data from keyboard and send to translator
        word = input()
        transSocket.send(word.encode())
    else:
        inputs = [transSocket, streamOther]
        readable, _, _ = select.select(inputs, [], [], 0)
        if readable:
            for s in readable:
                if s is transSocket:
                    # get data from translator and send to other speaker
                    word = transSocket.recv(net.BUFFER_SIZE)
                    streamOther.send(word)
                if s is streamOther:
                    # get data from other speaker and display
                     word = streamOther.recv(net.BUFFER_SIZE)
                     print(word.decode())

