# Author: Lukas Gdanietz de Diego

# import math
# import numpy

from typing import Iterable, Optional, Union

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting


adxl_register_dict = {
    0x00: {'name': 'DEVID'},
    0x1D: {'name': 'THRESH_TAP'},
    0x1E: {'name': 'OFSX'},
    0x1F: {'name': 'OFSY'},
    0x20: {'name': 'OFSZ'},
    0x21: {'name': 'DUR'},
    0x22: {'name': 'Latent'},
    0x23: {'name': 'Window'},
    0x24: {'name': 'THRESH_ACT'},
    0x25: {'name': 'THRESH_INACT'},
    0x26: {'name': 'TIME_INACT'},
    0x27: {'name': 'ACT_INACT_CTL'},
    0x28: {'name': 'THRESH_FF'},
    0x29: {'name': 'TIME_FF'},
    0x2A: {'name': 'TAP_AXES', 'structure':[None, None, None, None, 'Suppress', 'TAP_X Ena', 'TAP_Y Ena', 'TAP_Z Ena']},
    0x2B: {'name': 'ACT_TAP_STATUS', 'structure':[None, 'ACT_X', 'ACT_Y', 'ACT_Z', 'Asleep', 'TAP_X', 'TAP_Y', 'TAP_Z']},
    0x2C: {'name': 'BW_RATE', 'structure':[None, None, None, 'LOW_POWER', 'Rate_3', 'Rate_2', 'Rate_1', 'Rate_0']},
    0x2D: {'name': 'POWER_CTL', 'structure':[None, None, 'Link', 'AUTO SLEEP', 'Measure', 'Sleep', 'Wakeup mode_1', 'Wakeup mode_0']},
    0x2E: {'name': 'INT_ENABLE', 'structure':['DATA_READY', 'SINGLE TAP', 'DOUBLE TAP', 'Activity', 'Inactivity', 'FREE_FALL', 'Watermark', 'Overrun']},
    0x2F: {'name': 'INT_MAP', 'structure':['DATA_READY', 'SINGLE TAP', 'DOUBLE TAP', 'Activity', 'Inactivity', 'FREE_FALL', 'Watermark', 'Overrun']},
    0x30: {'name': 'INT_SOURCE', 'structure':['DATA_READY', 'SINGLE TAP', 'DOUBLE TAP', 'Activity', 'Inactivity', 'FREE_FALL', 'Watermark', 'Overrun']},
    0x31: {'name': 'DATA_FORMAT', 'structure':['SELF_TEST', 'SPI 3 Wire Mode', 'Interrupt Invert', None ,'Full Resolution', 'Justify Left', 'Range_1', 'Range_0']},
    0x32: {'name': 'DATAX0'},
    0x33: {'name': 'DATAX1'},
    0x34: {'name': 'DATAY0'},
    0x35: {'name': 'DATAY1'},
    0x36: {'name': 'DATAZ0'},
    0x37: {'name': 'DATAZ1'},
    0x38: {'name': 'FIFO_CTL', 'structure': ['FIFO_MODE_1', 'FIFO_MODE_0', 'Triger', 'Sample_4', 'Sample_3', 'Sample_2', 'Sample_1', 'Sample_0']},
    0x39: {'name': 'FIFO_STATUS', 'structure': ['FIFO_Triger', None, 'Entries_5', 'Entries_4', 'Entries_3', 'Entries_2', 'Entries_1', 'Entries_0']},
    0x3A: {'name': 'TAP_SIGN'},             # ADXL344 and ADXL346 only
    0x3B: {'name': 'ORIENT_CONF'},          # ADXL344 and ADXL346 only
    0x3C: {'name': 'ORIENT'}                # ADXL344 and ADXL346 only
}

def get_reg_name(address: int) -> str:
    try:
        return adxl_register_dict[address]['name']
    except KeyError:
        return f"0x{address:02X}"

def decode_message(address: int, byte: int, chip_reg_cnt: int) -> str:
    string = ""
    number: int = 0
    try:
        #structure = adxl_register_dict[address + chip_reg_cnt]['structure']
        structure = adxl_register_dict[address]['structure']
        string += f"0x{byte:02X}"
        for i, bit_name in enumerate(structure):
            if (byte >> (7 - i) & 0b1):
                if(bit_name[-1].isdigit()):
                    if(bit_name[-1] == '0'):
                        if string != "":
                            string += " | "
                        string += bit_name[:-2] + ": " +str(number)
                        number = 0
                    else:
                        number += 0b1 << int(bit_name[-1])
                else:
                    if string != "":
                        string += " | "
                    string += bit_name
                
        return string
    except KeyError:
        return f"0x{byte:02X}"
    #finally:
    #    return "Fail to parse"



class Hla(HighLevelAnalyzer):
    """ adxl Decoder """
    result_types = {
        "register": {"format": "{{data.rw}} {{data.reg}} : {{data.desc}}"},
    }
    def __init__(self):
        """Initialize HLA."""
        # Previous frame type
        # https://support.saleae.com/extensions/analyzer-frame-types/spi-analyzer
        self._previous_type: str = ""
        # current address
        self._address: Optional[int] = None
        # current access type
        self._rw: str = ""
        # Single or Multiple Operations
        self._mb: str = ""
        # current byte position
        self._byte_pos: int = 0
        # current chip reg counter
        self._mb_cnt: int = -1


        self._start_of_address_frame = None
    
    def decode(self, frame: AnalyzerFrame) -> Optional[Union[Iterable[AnalyzerFrame], AnalyzerFrame]]:
        """Decode frames."""
        is_first_byte: bool = self._previous_type == "enable"
        self._previous_type: str = frame.type

        if is_first_byte:
            self._byte_pos = 0
            self._mb_cnt = -1
        else:
            self._byte_pos += 1
            if self._mb.lower() == "multiple bytes": 
                self._mb_cnt += 1
        
        if frame.type != "result":
            return None
        
        mosi: bytes = frame.data["mosi"]
        miso: bytes = frame.data["miso"]

        if self._byte_pos == 0:
            try:
                self._address = (mosi[0] & 0b00111111)
                self._rw = "Read" if ((mosi[0] >> 7) & 0b1 ==  0b1) else "Write"
                self._mb = "Multiple Bytes " if ((mosi[0] >> 6) & 0b1 == 0b1) else "Single Byte "
            except IndexError:
                return None
            self._start_of_address_frame = frame.start_time
            return None
        if self._byte_pos > 0:
            name = self._mb + get_reg_name(self._address)
            if self._rw.lower() == "write":
                try:
                    byte = mosi[0]
                except IndexError:
                    return None
            else:
                try:
                    byte = miso[0]
                except IndexError:
                    return None
            #Now we decode the value of the byte, from the data we had before
            desc = decode_message(self._address, byte, self._byte_pos)
            # At the end we return the decoded frame:
            return AnalyzerFrame(
                "register",
                start_time = self._start_of_address_frame,
                end_time = frame.end_time,
                data = {
                    "reg": name,
                    "rw" : self._rw,
                    "desc": desc,
                }
            )
            
            
                


