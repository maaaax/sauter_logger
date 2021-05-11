#!/usr/bin/python3
import serial
import re
from time import sleep
import argparse
from datetime import datetime

import signal
import sys
signal.signal(signal.SIGINT, lambda sig,frame: sys.exit(0))

PORT='/dev/ttyUSB0'
BAUDRATE=2400
TIMEOUT=0.1 # ?
STRFTIME='%Y-%m-%d %H:%M:%S'



##########################################
def subbits(byte,mask,r_shift):
    return (byte & mask) >> r_shift

def is_maxhold(ctrl):
    maxhold_bits = subbits(ctrl,0b00110000,4)
    if maxhold_bits == 0b10:
        return True
    elif maxhold_bits == 0b01:
        return False
    return None

def modetxt(ctrl):
    if subbits(ctrl,0b00001100,2) == 0b10:  # Leq mode
        slowmode = subbits(ctrl,0b00000010,1) == 0b1
        basedon_minutes = subbits(ctrl,0b00000001,0) == 0b1
        Leq_mode = True
    else:
        slowmode = subbits(ctrl,0b00000001,0) == 0b1
        basedon_minutes = None
        Leq_mode = False

    non_Leq_modes={
            0b000: 'Lp (dB), Weighting A',
            0b001: 'Lp (dB), Weighting C',
            0b010: 'Lp (dB), Flat',
            0b011: 'Ln (%), Weighting A',
            0b101: 'Unknown',
            0b110: 'Cal (dB)'
            }
    if Leq_mode:
        txt = 'Leq (dB), Weighting A'
        if basedon_minutes:
            txt+=', based on minutes'
        else:
            txt+=', based on 10s'
    else:
        txt = non_Leq_modes[subbits(ctrl,0b00001110,1)]

    if slowmode:
        txt+=', Slow'
    else:
        txt+=', Fast'

    if is_maxhold(ctrl):
        txt+=', MaxHold'
    return txt

def chkchksum(msg):
    if len(msg)<=2: return False
    return int(msg[-1]) == (sum(x for x in msg[:-1]) % 256)

def decode_msg(msg):
    m = re.match(b'^\x08\x04(?P<ctrl>.)\x0a\x0a(?P<value>...)\x01$', msg[:-1])
    if not m:
        return None

    d=m.groupdict()
    try:
        val="%0.1f" % (d['value'][0]*10+d['value'][1]+d['value'][2]/10)
    except:
        val=None

    return (val,modetxt(ord(d['ctrl'])))


##########################################

MULTILINE=20

parser = argparse.ArgumentParser(description='Sauter SU logger')
parser.add_argument('-d', '--device', required=False, default=PORT, help='serial device (default: '+PORT+')')
parser.add_argument('-s', '--singleline', action='store_true', default=False, required=False, help='print mode in every line')
parser.add_argument('-m', '--printmode', action='store_true', default=False, required=False, help='print mode and exit')
parser.add_argument('-t', '--timeformat', default=STRFTIME, required=False, help='time format')
args=parser.parse_args()

ser = serial.Serial()
ser.baudrate = BAUDRATE
ser.port = PORT
ser.timeout = TIMEOUT

ser.open()
lastmsg=""
while True:

### wait for heartbeat from device

     char = ser.read()
     if char==b'\x10': # heartbeat
         #print("hb received")
         ser.write(b'\x20')
     elif char==b'': continue
     else: # out of sync?
         sleep(1)
         continue
     #print(char)

### read message

     msg=bytes()
     while True:
         char = ser.read()
         if char==b'':
             #print("timeout")
             break
         msg+=char

### check chksum
     if len(msg)<1:
         print("# no message received")
         continue

     if not chkchksum(msg):
         print("# chksum error, msg: "+str(msg))
         #print("# chksum error")
         continue

### decode

     dt=datetime.now().strftime(args.timeformat)

     val,msg = decode_msg(msg)
     if args.printmode:
         print(msg)
         sys.exit(0)
     if args.singleline:
         print(val+';'+dt+';'+msg,flush=True)
     else:
         if lastmsg!=msg:
             print("# "+msg,flush=True)
         print(val+';'+dt,flush=True)

     lastmsg=msg
