import sys
import socket
import selectors
import types
import base64
import binascii
import hashlib

sel = selectors.DefaultSelector()

websocketkey = 'x3JJHMbDL1EzLkh9GBhXDw=='
raw_key = base64.b64decode(websocketkey.encode(), validate=True)
key = base64.b64encode(raw_key).decode()
GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
sha1 = hashlib.sha1((key + GUID).encode()).digest()
websocketacceptkey = base64.b64encode(sha1).decode()
print('Key:', websocketacceptkey)

def decode_frame(frame):
    opcode_and_fin = frame[0]
    payload_len = frame[1]
    print(payload_len)
    encrypted_payload = frame [2: payload_len]
    payload = bytearray([ encrypted_payload[i]  for i in range(payload_len - 2)])
    print(payload)
    return payload


def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    print("accepted connection from", addr)
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"", websock=0)
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        payload = sock.recv(1024)  # Should be ready to read
        bytearraypayload = bytearray(payload)
        if len(bytearraypayload) != 0:
            if bytearraypayload[0] != 0:
                recv_data = payload.decode('utf-8')
            else:
                payload = decode_frame(bytearray(payload))
                recv_data = payload.decode('utf-8')
                print('Data: ', recv_data)
        else:
            recv_data = payload.decode('utf-8')
        if recv_data:
            string_list = recv_data.split(' ')     # Split request from spaces
            method = string_list[0]
            requesting_file = string_list[1]
            requesting_file = requesting_file.lstrip('/')
            print('Client request', recv_data)
            file = open('index.html','rb') # open file , r => read , b => byte format
            response = file.read()
            file.close()
            if requesting_file == 'chat' and method == "GET":
                header = 'cHTTP/1.1 101 Switching Protocols\r\n' + 'Upgrade: websocket\r\n' + 'Connection: upgrade\r\n'
+ 'Sec-WebSocket-Accept: %s\r\n' % websocketacceptkey + 'Sec-WebSocket-Protocol: chat\r\n'
                final_response = header.encode('utf-8')
                data.outb += final_response
                data.websock = 1
            elif method == 'PUT':
                header = "bHTTP/1.1 socketongoing\r\n"
                final_response = header.encode('utf-8')
                data.outb += final_response
                data.websock = 1
            else:
                header = 'HTTP/1.1 200 OK\n'
                mimetype = 'text/html'
                header += 'Content-Type: '+str(mimetype)+'\n\n'
                final_response = header.encode('utf-8')
                final_response += response
                data.outb += final_response
                print(data.outb)
                data.websock = 0
    if mask & selectors.EVENT_WRITE:
        if data.outb:
            checksignal = data.outb.decode('utf-8')
            if checksignal[0] == 'c':
                answer = checksignal[1:]
                print("echoing", repr(data.outb), "to", data.addr)
                sent = sock.send(answer.encode('utf-8'))
                data.outb = data.outb[sent:]
            elif checksignal[0] == 'b':
                answer = checksignal[1:]   
                frame = [0]
                frame += [len(answer)]
                frame_to_send = bytearray(frame) + bytearray(answer, 'utf-8')
                print("echoing", repr(data.outb), "to", data.addr)
                print('coonection is ongoing', answer)
                sent = sock.send(frame_to_send)
                data.outb = data.outb[sent:]
            else:
                print("echoing", repr(data.outb), "to", data.addr)
                print('WebSock:', data.websock)
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]
                if data.websock == 0:
                    print("closing connection to", data.addr)
                    sel.unregister(sock)
                    sock.close()


if len(sys.argv) != 3:
    print("usage:", sys.argv[0], "<host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
lsock.bind((host, port))
lsock.listen()
print("listening on", (host, port))
lsock.setblocking(False)
sel.register(lsock, selectors.EVENT_READ, data=None)

try:
    while True:
        events = sel.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                accept_wrapper(key.fileobj)
            else:
                service_connection(key, mask)
except KeyboardInterrupt:
    print("caught keyboard interrupt, exiting")
finally:
    sel.close()
