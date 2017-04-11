import struct
import socket
import sys

class Dirservice:
    def decode_client_msg(self, msg):
        tuple = struct.unpack('!16s16s16s',msg)
        (UID,user_addr,DID) = tuple
        UID = UID.decode('utf-8')
        DID = DID.decode('utf-8')
        user_addr = user_addr.decode('utf-8')
        return (UID,user_addr,DID)

    def encode_client_msg(self, error_code, msg):
        msg = msg + ' ' * (16 - len(msg))
        return struct.pack('!H16s', error_code, msg.encode('utf-8'))


    def table_add(self, uid, user_addr, table):
        table[uid] = user_addr

    def table_lookup(self, uid, table):
        return table[uid]

if  __name__ =='__main__':
    d = Dirservice()
    table = dict()
    dirList = sys.argv[1].split(':')
    dirIP = dirList[0]
    dirPort = int(dirList[1])

    sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sockTCP.bind((dirIP, dirPort))
    sockTCP.listen(1)
    conn, addr = sockTCP.accept()
    while 1:
        print('Connection address:', addr)
        data = conn.recv(48)
        if not data:
            break
        else:
            decoded = d.decode_client_msg(data)[-1]
            if table.get(decoded) != None:
                reply = d.encode_client_msg(400, table[decoded])
            else:
                reply = d.encode_client_msg(600, '')
            conn.send(reply)
    conn.close()