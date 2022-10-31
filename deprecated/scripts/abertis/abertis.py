#!/usr/bin/python
# @oottppxx, 2022-10-31


from __future__ import print_function

import os
import sys

pid = 0

usage = False
try:
    argc = len(sys.argv)
    if (argc > 2):
        usage = True
    elif argc == 2:
        if (sys.argv[1].find('h') != -1):
            usage = True
        else:
            pid = int(sys.argv[1], 10)
except:
    usage = True

if usage:
    print("Usage: %s <PID>" % sys.argv[0], file=sys.stderr)
    sys.exit(1)

try:
    ts_in = os.fdopen(os.dup(sys.stdin.fileno()), "rb")
    ts_out = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
except:
    print("Error mangling stdin/stdout!", file=sys.stderr)
    sys.exit(1)

def byte_value(x):
    try:
        return ord(x)
    except:
        return x

while (True):
    packet = ts_in.read(188)
    if len(packet) != 188:
        break
    # Process packet if PID argument was undefined or zero;
    # Process packet if PID argument defined, not zero, and matches packet PID;
    # Skip otherwise.
    if (pid == 0) or (pid == (((byte_value(packet[1])&0x1f)<<8) | byte_value(packet[2]))):
        skip = 0
        afc = byte_value(packet[3])&0x30
        if (afc == 0x10):
            # AFC = '01', no adaptation field, payload only.
            # Skip TS 4 byte header only.
            skip = 4
        elif (afc == 0x30):
            # AFC = '11', adaptation field present.
            # Skip TS 4 byte header;
            # Also skip the adaptation field length byte;
            # Also skip the adaptation field bytes following.
           skip = 5 + byte_value(packet[4])
        # Emit bytes if AFC was:
        #    '01' (no adaptation field, payload only);
        #    '11' (adaptation field followed by payload).
        # Ignore packet if AFC was:
        #    '10' (no payload);
        #    '00' (reserved for future use).
        if skip:
            ts_out.write(packet[skip:])
        
