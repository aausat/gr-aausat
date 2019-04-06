#!/usr/bin/env python
# -*- coding: utf-8 -*-
# The MIT License (MIT)
# 
# Copyright (c) 2016 Daniel Estévez
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 

import numpy
from gnuradio import gr
import pmt
import fec

class aausat4_fec_encoder(gr.basic_block):
    """
    docstring for block aausat4_fec_encoder
    """
    def __init__(self, syncword, training_len=60, hmac=None, verbose=False):
        gr.basic_block.__init__(self,
            name="aausat4_fec_encoder",
            in_sig=[],
            out_sig=[])
        self.verbose = verbose
        self.syncword = syncword
        self.training_len = training_len
        self.message_port_register_in(pmt.intern('in'))
        self.set_msg_handler(pmt.intern('in'), self.handle_msg)
        self.message_port_register_out(pmt.intern('out'))

        self.ec = fec.PacketHandler(hmac)

    def handle_msg(self, msg_pmt):
        msg = pmt.cdr(msg_pmt)
        if not pmt.is_u8vector(msg):
            print "[ERROR] Received invalid message type. Expected u8vector"
            return
        data = str(bytearray(pmt.u8vector_elements(msg)))
        if self.verbose:
            print "Data length: {}".format(len(data))

        fsm = '\x59' # Long packet
        if len(data) <= 23:
            # Short packet
            fsm = '\xa6'
        elif len(data) > 84:
            print "Packet too long ({})".format(len(data))
            # Cut
            data = data[0:84]

        # Add length field
        datalen = len(data)
        if self.ec.key:
            datalen += 2 # 2 byte hmac

        

        # Add dummy CSP header
        csp_header = str(bytearray.fromhex('{:08x}'.format(0)))
        data = csp_header + data

        # Add length field (non including CSP header)
        data = str(bytearray.fromhex('{:04x}'.format(datalen))) + data

        out_data = None
        try:
            out_data = self.ec.frame(data)
        except Exception as ex:
            print(ex)

        if out_data:
            # Add training, syncword, FSM
            training = str(bytearray([0x55]*self.training_len))
            out_data = training + str(self.syncword) + fsm + out_data
            self.message_port_pub(pmt.intern('out'),
                                  pmt.cons(pmt.PMT_NIL,
                                           pmt.init_u8vector(len(out_data), bytearray(out_data))))


