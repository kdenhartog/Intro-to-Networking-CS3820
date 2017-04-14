import os
import socket
import select
import sys
import re
import Queue
import urlparse

#Helper function to locate the proper directory where html files are stored
def http_get_parse(req):
    get_line = req.split('\n')[0]
    (action, uri, http_version) = get_line.split(' ')
    if uri == "/":
        uri += 'index.html'
    uri = uri[1:]
    uri_complete = os.path.join('static/',uri)
    return uri_complete

#Helper function to validate the URI in the header
def uri_regex(uri):
    regex = re.compile(r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if re.match(regex, uri) == None:
        return False
    else:
        return True
#Helper function to validate all key:value pairs in the Header
def key_value_check(line):
    if "localhost:" in line:
        l = line.split(':')
        if len(l) == 3:
            return True
        else:
            return False
    if ':' in line:
        return True
    else:
        return False

#Helper function to validate that there is a file at the specified URI
#This will return a reply containing the entire 200 OK response if a file is found
#otherwise it will return a reply containing a 404 Response
def uri_lookup(uri):
    header = "HTTP/1.1 200 OK\r\nContent-Type: text/HTML\r\n\r\n"
    body = ''
    try:
        with open(uri, "rb") as f:
            byte = f.read()
            body = byte.decode("utf-8")
            print(byte)
            reply = (header + body).encode()
    except:
        header = "HTTP/1.1 404 Not Found\r\nContent-Type: text/HTML\r\n\r\n"
        reply = header.encode()
    finally:
        return reply

#This is a helper function to return a 500 Response
def bad_request():
    header = "HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/HTML\r\n\r\n"
    reply = header.encode()
    return reply

#returns a URI if the Header is consider valid
#otherwise returns None if the Header is consider invalid
def process_http_header(message, cSocket):
    get_first_line = message.splitlines(True)[0]
    try:
        (action, uri, http_version) = get_first_line.split(' ')
    except:
        return None
    if "GET" == action: #state1, 2, and 3 check
        print("Passed state1")
        if uri_regex(uri):
            print("Passed state2")
            if "HTTP/1.1\r\n" == http_version:
                print("Passed state3")
                line_split = message.splitlines(True)
                del line_split[0]
                for i in line_split:
                    if i == "\r\n":
                        print("Passed state4")
                        return http_get_parse(message) #Header valid
                    if key_value_check(i) == False:
                        print("Failed State4")
                        return None
            else:
                print("Failed State3")
                return None
        else:
            print("Failed State2")
    else:
        print("Failed State1")
        return None #state1, 2, or 3 Failed

def main():
    #Arguement error testing
    if len(sys.argv) != 3:
        print("Wrong host and port")
        sys.exit(0)
    else:
        host = sys.argv[1]
        port = int(sys.argv[2])
        print("Starting web server")

    #Start Server and bind to port
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.bind((host,port))
    #Listen for connections that are incoming
    server.listen(5)

    #process header that was received and handles connection syncing and responses
    while True:
        # Sockets from which we expect to read
        inputs = [server]
        # Sockets to which we expect to write
        outputs = [ ]
        # Outgoing message queues (socket:Queue)
        message_queues = {}
        while inputs:
            (readable, writable, exceptional) = select.select(inputs, outputs, inputs)
            for s in readable:
                if s is server:
                    (cSocket, address) = s.accept()
                    cSocket.setblocking(0)
                    #Append
                    inputs.append(cSocket)
                    message_queues = {}
                else:
                    #Receive data and ecode
                    x = s.recv(1024)
                    dataRecv = x.decode("utf-8")
                    #Store data in queue
                    if s in message_queues:
                        currentData = message_queues.get(s) + dataRecv
                    else:
                        message_queues[s] = dataRecv
                        currentData = message_queues.get(s)
                    #Check if the end of the header has been received
                    if s not in outputs:
                        outputs.append(s)
                    if "\r\n\r\n" in currentData:
                        header = process_http_header(currentData, cSocket)
                        if header == None: #Handles bad requests
                            reply = bad_request()
                            reply = reply.encode("UTF-8")
                            s.send(reply) #Send response
                            if s in outputs:
                                outputs.remove(s)
                            inputs.remove(s)
                            s.close() #close connection
                            del message_queues[s]
                        else: #Handles valid headers
                            reply = uri_lookup(header)
                            reply = reply.encode("UTF-8")
                            s.send(reply)
                            if s in outputs:
                                outputs.remove(s)
                            inputs.remove(s)
                            s.close()
                            del message_queues[s]

if __name__ == "__main__":
    main()
