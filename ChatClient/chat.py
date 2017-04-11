import select
import socket
import sys
import struct
import time


"""
This is used to configure a chat connection between two chat users
"""
class Chat:
    def __init__(self):
        arg2List = sys.argv[2].split(':')
        if ':' in sys.argv[3]:
            arg3List = sys.argv[3].split(':')
            self.destUser = "No Name"
            self.destIP = arg3List[0]
            self.destPort = int(arg3List[1])
        else:
            self.destUser = sys.argv[3]
            self.destIP = ""
            self.destPort = 0
        arg4List = sys.argv[4].split(':')

        self.srcUser = sys.argv[1]
        self.srcIP = arg2List[0]
        self.srcPort = int(arg2List[1])

        self.regIP = arg4List[0]
        self.regPort = int(arg4List[1])
        self.seqnum = 0

    def encode_chat_msg(self, uid, did, msg, version=150):
        uid = uid + ' ' * (16 - len(uid))
        did = did + ' ' * (16 - len(did))
        self.seqnum = self.seqnum + 1
        header_buf = struct.pack('!HH16s16s', version, self.seqnum, uid.encode('utf-8'), did.encode('utf-8'))
        header_buf = header_buf + msg.encode('utf-8')
        return header_buf

    def decode_msg(self,msg_buf):
        tuple = struct.unpack('!HH16s16s', msg_buf[:36])
        (version, seqnum, UID, DID) = tuple
        UID = UID.decode('utf-8')
        DID = DID.decode('utf-8')
        msg = msg_buf[36:].decode('utf-8')
        return (seqnum, UID, DID, msg)

    def encode_registration(self, uid, user_addr, dest_addr):
        uid = uid + ' ' * (16 - len(uid))
        return struct.pack('!16s16s16s', uid.encode('utf-8'), user_addr.encode('utf-8'), dest_addr.encode('utf-8'))

    def decode_registration(self, msg_buf):
        tuple = struct.unpack('!H16s',msg_buf)
        (err_code, dest_addr) = tuple
        if err_code == 600:
            return True
        else:
            addrList = dest_addr.split(':')
            self.destIP = addrList[0]
            self.destPort = int(addrList[1])
            return False



"""
This is the main method which contains the program
"""
if  __name__ =='__main__':
    c = Chat()

    #Regustration phase
    if ":" not in sys.argv[3]:
        sockTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sockTCP.connect((c.regIP,c.regPort))
        #print >> sys.stderr, 'connecting to %s port %s' % (c.regIP,c.regPort)
        reg_msg = c.encode_registration(c.srcUser, sys.argv[2], sys.argv[4]) #encodes message to dirservice
        #print >> sys.stderr, 'sending "%s"' % reg_msg
        sockTCP.sendall(reg_msg)
        repeat = True#test variable to identify if successful registration lookup
        while True:
            reg_recv = sockTCP.recv(18)
            repeat = c.decode_registration(reg_recv)
            print("Name not found in Directory. Waiting for 5 seconds.")
            time.sleep(5)
        sockTCP.close()

    #Chat client phase
    sockUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockUDP.bind((c.srcIP, c.srcPort))

    while True:
        msg = None
        r, w, x = select.select([sockUDP, sys.stdin], [], [])

        #Used to test if message is in stdin, if it is encode message and send
        if sys.stdin in r:
            msg = input()

            #Exits if exit command is given with argument of 1, this will close both clients connections
            if "exit(1)" in msg:
                print("Chat Connection Closed")
                msg_bytes = c.encode_chat_msg(c.srcUser, c.destUser, c.srcUser + " closed the connection.")
                sent = sockUDP.sendto(msg_bytes, (c.destIP, c.destPort))
                sockUDP.close()
                exit(1)

            print('sending "%s"' % msg)
            msg_bytes = c.encode_chat_msg(c.srcUser,c.destUser,msg)
            sent = sockUDP.sendto(msg_bytes, (c.destIP, c.destPort))


        #used to test if a message has been received from the specified socket, if so decodes and prints to stdin
        if sockUDP in r:
            recv_pkt, server = sockUDP.recvfrom(4096)
            data = c.decode_msg(recv_pkt)[-1]

            #tests if the other user closed the connection and automatically closes your connection
            if "closed the connection." in data:
                print('received "%s"' % data)
                print("Closing connection now.")
                sockUDP.close()
                exit(1)

            print('received "%s"' % data)


