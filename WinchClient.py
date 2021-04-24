#!/usr/bin/env python

import socket
#import tkinter
import threading
from time import sleep

UDP_IP = "127.0.0.1"
UDP_PORT = 5008
print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)

sock = socket.socket(socket.AF_INET,  # Internet
                     socket.SOCK_DGRAM)  # UDP

while True:
    cmd = raw_input("Command: ")
    for i in range(50):
        print("sending command:", cmd)
        sock.sendto(str.encode(cmd), (UDP_IP, UDP_PORT))
        sleep(.1)

# def send_command():
#     global command
#     print("sending command:", command)
#     while toggle_btn.config('relief')[-1] == 'sunken':
#         sock.sendto(str.encode(command), (UDP_IP, UDP_PORT))
#
#
# def toggle():
#     x = threading.Thread(target=send_command)
#     if toggle_btn.config('relief')[-1] == 'sunken':
#         toggle_btn.config(relief="raised")
#     else:
#         threading.send_command()
#         toggle_btn.config(relief="sunken")
#
#
#
# master = tkinter.Tk()
# master.title("pack() method")
# commands = ["MANIN", "MANOUT", "CAST", "REPORTPOSITION"]
# for command in commands:
#     # button = tkinter.Button(master, text=command, width=20, height=5)
#     command = command
#     toggle_btn = tkinter.Button(text=command, width=20, relief="raised", command=toggle)
#
#     t = threading.Timer(0.09, command=send_command)
#     toggle_btn.bind('<ButtonPress-1>', lambda event, command=command: t.start())
#     toggle_btn.bind('<ButtonRelease-1>', lambda event, command=command: t.cancel())
#     toggle_btn.pack(side=tkinter.TOP)
#
# master.mainloop()
