import net
import socket

SHUTDOWN_SERVER     = "11"

LOCAL_HOST_IP_ADDR = socket.gethostbyname(socket.gethostname())  # Local host IP address
SERVER = ("192.168.1.189", 65430)

toServerSocket = net.ConnectedReqRepSocket(LOCAL_HOST_IP_ADDR, SERVER)
data = SHUTDOWN_SERVER
toServerSocket.send(data.encode())
toServerSocket.close()