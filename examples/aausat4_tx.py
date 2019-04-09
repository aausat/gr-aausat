#!/usr/bin/env python

import sys
import pmt
import zmq
import fileinput

if __name__ == '__main__':
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind("tcp://127.0.0.1:44445")

    for line in fileinput.input():
        send_str = line.rstrip()
        msg = pmt.make_u8vector(len(send_str), ord(' '))
        for i in range(len(send_str)):
            pmt.u8vector_set(msg, i, ord(send_str[i]))
        pdumsg = pmt.cons(pmt.make_dict(), msg)
        serialized = pmt.serialize_str(pdumsg)
        socket.send(serialized)
