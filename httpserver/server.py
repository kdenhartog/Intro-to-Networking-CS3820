import os
import socket
import sys
import re

def http_get_parse(req):
    get_line = req.split('\n')[0]
    (action, uri, http_version) = get_line.split(' ')
    print(uri)
    pass

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Wrong host and port")
        sys.exit(0)
    else:
        hostname = sys.argv[1]
        port = int(sys.argv[2])
        print("Starting web server")

    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.bind((hostname,port))

    serversocket.listen(5)
    while True:
        (clientsocket, address) = serversocket.accept()
        x = clientsocket.recv(1024)
        x = x.decode("utf-8")
        print(str(x))
        uri = http_get_parse(x)
        fn = os.path.join('static',uri)
        header = "HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n"
        body = ''
        print("reading file", fn)
        try:
            with open(fn, "rb") as f:
                byte = f.read()
            # byte += bytes.decode("utf-8")
            # while len(byte) != 0:
            #     byte = f.read(100)
            #     byte += bytes.decode("utf-8")
                body = byte.decode("utf-8")
                print(byte)
                print("sending")
                reply = (header + body).encode()
                clientsocket.send(reply)
        except:
            error = True
            if error:
                header = "404 HEADER\r\n\r\n"
                reply = error.encode()
                clientsocket.send(reply)
        finally:
            clientsocket.close()