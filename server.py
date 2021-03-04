import socket

HOST = '127.0.0.1'  # Standard loopback interface address (localhost)
PORT = 65432        # Port to listen on (non-privileged ports are > 1023)

def getStreamSocket():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        conn, _ = s.accept()
    return conn

def RecData(conn):
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            s = repr(data.decode("utf-8"))
            print("Received", s)
            conn.sendall(b"Receiver's reply " + data)

print("Waiting for a client")
conn = getStreamSocket()
print("connected and receiving")
RecData(conn)

