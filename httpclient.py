import socket
import time
import datetime

target_host = "X.X.X.X" # your AGW frontend Public IP
 
target_port = 80  # create a socket object 
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  

def decode_frame(frame):
        opcode_and_fin = frame[0]

        payload_len = frame[1] #- 128

        print(payload_len)

        encrypted_payload = frame [2 : payload_len]

        payload = bytearray([ encrypted_payload[i] for i in range(payload_len - 2)])
        
        return payload

# connect the client 
client.connect((target_host,target_port))  
 
# send some data 
request = "GET /chat HTTP/1.1\r\nHost:%s\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==\r\nSec-WebSocket-Protocol: chat, superchat\r\nSec-WebSocket-Version: 13\r\n\r\n" % target_host
close = "GET /index.html HTTP/1.1\r\nHost:%s\r\n\r\n" % target_host
data = "PUT /chat HTTP/1.1\r\nHost:\r\n\r\n" #% target_host
frame = [0]
frame += [len(data)]
frame_to_send = bytearray(frame) + bytearray(data, 'utf-8')
mark = 0

while True:
    val = input("run again?")
    if val == "no":
        client.send(close.encode())
        response = client.recv(4096)  
        http_response = repr(response)
        print(http_response)
        client.close()
        break
    else:
        if mark == 1:
            print(datetime.datetime.now())
            while True:
                try:
                    client.send(frame_to_send)
                    response = client.recv(4096)
                    http_response = response.decode('utf-8')
                    time.sleep(2)             
                except:
                    print(datetime.datetime.now())
                    raise
        else:
            client.send(request.encode())  
            # receive some data 
            response = client.recv(4096)
            http_response = response.decode('utf-8')
            print('response', http_response)
            mark = 1
