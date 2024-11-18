"""
Embedded Python Blocks:

Each time this file is saved, GRC will instantiate the first class it finds
to get ports and parameters of your block. The arguments to __init__  will
be the parameters. All of them are required to have default values!
"""

import numpy as np
from gnuradio import gr
import pmt


class blk(gr.sync_block):  # other base classes are basic_block, decim_block, interp_block
    """Embedded Python Block example - a simple multiply const"""

    def __init__(self):  # only default arguments here
        """arguments to this function show up as parameters in GRC"""
        gr.sync_block.__init__(
            self,
            name='GUI data handling',   # will show up in GRC
            in_sig=None,
            out_sig=[np.single]
        )
        # if an attribute with the same name as a parameter is found,
        # a callback is registered (properties work, too).
        self.message_port_register_in(pmt.intern('message_in'))
        self.image_portName = 'image_portName'
        self.set_msg_handler(pmt.intern('message_in'), self.handle_msg)
        self.message_port_register_out(pmt.intern(self.image_portName))
        self.tx_beam_id = 0

    def work(self, input_items, output_items):
        """example: multiply with constant"""
        output_items[0][:] = self.tx_beam_id


        return len(output_items[0])

    def handle_msg(self, msg):
        if pmt.dict_has_key(msg, pmt.string_to_symbol("tx_beam_id")):
            r = pmt.dict_ref(msg, pmt.string_to_symbol("tx_beam_id"), pmt.PMT_NIL)
            if pmt.to_long(r) < 22:
                self.tx_beam_id = pmt.to_long(r)
                PMT_beam = pmt.string_to_symbol('/home/inets/Workspace/beam_plots/beamId_' + str(self.tx_beam_id) + '.png')
                PMT_msg = pmt.cons(pmt.from_bool(True), PMT_beam)
                self.message_port_pub(pmt.intern(self.image_portName), PMT_msg)

