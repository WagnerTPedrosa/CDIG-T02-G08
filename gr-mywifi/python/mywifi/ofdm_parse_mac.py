# SPDX-License-Identifier: GPL-3.0-or-later
# Simplified Python re-implementation of gr-ieee802-11 ofdm_parse_mac
import struct
from gnuradio import gr
import pmt

def _fmt_mac(b):
    return ":".join(f"{x:02x}" for x in b)

class ofdm_parse_mac(gr.basic_block):
    """
    Message-only block:
      - IN  (message): PDU (meta, bytes) or raw blob/u8vector
      - OUT (message): same PDU forwarded (unchanged)
    Prints parsed 802.11 MAC header when debug=True.
    """

    def __init__(self, debug=False):
        gr.basic_block.__init__(
            self,
            name="ofdm_parse_mac_py",
            in_sig=None,
            out_sig=None,
        )
        self.debug = bool(debug)

        self.message_port_register_in(pmt.intern("in"))
        self.message_port_register_out(pmt.intern("out"))
        self.set_msg_handler(pmt.intern("in"), self._handle_msg)

    # ------------------------- Core logic -------------------------

    def _handle_msg(self, msg):
        if pmt.is_eof_object(msg):
            self.message_port_pub(pmt.intern("out"), pmt.PMT_EOF)
            self.detail().get().set_done(True)
            return

        # Accept PDUs (pair(meta, vector)) or raw blob/u8vector
        meta = pmt.PMT_NIL
        pdu = msg
        if pmt.is_pair(msg):
            meta = pmt.car(msg)
            pdu = pmt.cdr(msg)

        # Extract bytes
        data = None
        if pmt.is_u8vector(pdu):
            data = bytearray(pmt.u8vector_elements(pdu))
        elif pmt.is_blob(pdu):
            # blob -> Python bytes
            data = bytearray(pmt.to_python(pdu))
        else:
            # Some blocks send PMT string; try generic conversion
            try:
                data = bytearray(pmt.to_python(pdu))
            except Exception:
                if self.debug:
                    print("ofdm_parse_mac_py: unsupported PMT type")
                return

        length = len(data)
        if length < 10:
            if self.debug:
                print("ofdm_parse_mac_py: frame too short")
            return

        # Try parse MAC header (minimum base header is 24 bytes)
        if length >= 24:
            # Frame Control (2), Duration (2), Addr1 (6), Addr2 (6), Addr3 (6), SeqCtrl (2)
            frame_control, duration = struct.unpack_from("<HH", data, 0)
            addr1 = bytes(data[4:10])
            addr2 = bytes(data[10:16])
            addr3 = bytes(data[16:22])
            seq_ctrl = struct.unpack_from("<H", data, 22)[0]

            if self.debug:
                stype = (frame_control >> 4) & 0xF
                ftype = (frame_control >> 2) & 0x3
                print(f"[MAC] len={length} fc=0x{frame_control:04x} type={ftype} stype={stype} dur={duration}")
                print(f"      addr1={_fmt_mac(addr1)}")
                print(f"      addr2={_fmt_mac(addr2)}")
                print(f"      addr3={_fmt_mac(addr3)}")
                print(f"      seqnum={seq_ctrl >> 4}")

                # Optional subtype print like the C++ (short version)
                if ftype == 0:
                    names = ["AssocReq","AssocResp","ReassocReq","ReassocResp","ProbeReq","ProbeResp",
                             "TimingAdv","Reserved","Beacon","ATIM","Disassoc","Auth","Deauth","Action","ActionNoAck","Reserved"]
                    print(f"      MGMT subtype={names[stype] if stype < len(names) else 'Unknown'}")
                elif ftype == 1:
                    cnames = {11:"RTS",12:"CTS",13:"ACK",9:"BlockACK",8:"BlockACKReq"}
                    print(f"      CTRL subtype={cnames.get(stype,'Other')}")
                elif ftype == 2:
                    dnames = {0:"Data",4:"Null",8:"QoS Data",12:"QoS Null"}
                    print(f"      DATA subtype={dnames.get(stype,'Other')}")

        # CRC check (FCS) if present
        if self.debug and length >= 4:
            ok = self._check_crc32_le(data)
            print(f"      CRC {'OK' if ok else 'FAIL'}")

        # Forward unchanged as a proper PDU (meta, bytes) for downstream blocks
        out_vec = pmt.init_u8vector(len(data), data)
        self.message_port_pub(pmt.intern("out"), pmt.cons(meta, out_vec))

    # 802.11 CRC32 over payload; FCS is last 4 bytes (little-endian)
    def _check_crc32_le(self, data: bytearray) -> bool:
        if len(data) < 4:
            return False
        poly = 0xEDB88320
        crc = 0xFFFFFFFF
        for byte in data[:-4]:
            crc ^= byte
            for _ in range(8):
                mask = -(crc & 1)
                crc = (crc >> 1) ^ (poly & mask)
        crc ^= 0xFFFFFFFF
        fcs = struct.unpack_from("<I", data, len(data) - 4)[0]
        return crc == fcs
