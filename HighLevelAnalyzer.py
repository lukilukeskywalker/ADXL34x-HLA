# Author: Lukas Gdanietz de Diego

# import math
# import numpy

from typing import Iterable, Optional, Union

from saleae.analyzers import HighLevelAnalyzer, AnalyzerFrame, StringSetting, NumberSetting, ChoicesSetting


adxl_register_dict = {
    0x00: {'name': 'DEVID',             'element': 0},
    0x1D: {'name': 'THRESH_TAP',        'element': 0, 'scale' : 62.5, 'signed': False, 'unit': 'mg'},
    0x1E: {'name': 'OFSX',              'element': 0, 'scale' : 15.6, 'signed': True, 'unit':'mg'},
    0x1F: {'name': 'OFSY',              'element': 0, 'scale' : 15.6, 'signed': True, 'unit':'mg'},
    0x20: {'name': 'OFSZ',              'element': 0, 'scale' : 15.6, 'signed': True, 'unit':'mg'},
    0x21: {'name': 'DUR',               'element': 0, 'scale' : 625, 'signed': False, 'unit':'uS'},
    0x22: {'name': 'Latent',            'element': 0, 'scale' : 1.25, 'signed': False, 'unit':'mS'},
    0x23: {'name': 'Window',            'element': 0, 'scale' : 1.25, 'signed': False, 'unit':'mS'},
    0x24: {'name': 'THRESH_ACT',        'element': 0, 'scale' : 62.5, 'signed': False, 'unit': 'mg'},
    0x25: {'name': 'THRESH_INACT',      'element': 0, 'scale' : 62.5, 'signed': False, 'unit': 'mg'},
    0x26: {'name': 'TIME_INACT',        'element': 0, 'scale' : 1, 'signed': False, 'unit':'S'},
    0x27: {'name': 'ACT_INACT_CTL',     'element': 0, 'structure': ['ACT AC/~DC', 'ACT_X ena', 'ACT_Y ena', 'ACT_Z ena', 'INACT AC/~DC', 'INACT_X ena', 'INACT_Y ena', 'INACT_Z ena']},
    0x28: {'name': 'THRESH_FF',         'element': 0, 'scale' : 62.5, 'signed': False, 'unit': 'mg'},
    0x29: {'name': 'TIME_FF',           'element': 0, 'scale' : 5, 'signed': False, 'unit':'mS'},
    0x2A: {'name': 'TAP_AXES',          'element': 0, 'structure':['None', 'None', 'None', 'None', 'Suppress', 'TAP_X Ena', 'TAP_Y Ena', 'TAP_Z Ena']},
    0x2B: {'name': 'ACT_TAP_STATUS',    'element': 0, 'structure':['None', 'ACT_X', 'ACT_Y', 'ACT_Z', 'Asleep', 'TAP_X', 'TAP_Y', 'TAP_Z']},
    0x2C: {'name': 'BW_RATE',           'element': 0, 'structure':['None', 'None', 'None', 'LOW_POWER', 'Rate_3', 'Rate_2', 'Rate_1', 'Rate_0']},
    0x2D: {'name': 'POWER_CTL',         'element': 0, 'structure':['None', 'None', 'Link', 'AUTO SLEEP', 'Measure', 'Sleep', 'Wakeup mode_1', 'Wakeup mode_0']},
    0x2E: {'name': 'INT_ENABLE',        'element': 0, 'structure':['DATA_READY', 'SINGLE TAP', 'DOUBLE TAP', 'Activity', 'Inactivity', 'FREE_FALL', 'Watermark', 'Overrun']},
    0x2F: {'name': 'INT_MAP',           'element': 0, 'structure':['DATA_READY', 'SINGLE TAP', 'DOUBLE TAP', 'Activity', 'Inactivity', 'FREE_FALL', 'Watermark', 'Overrun']},
    0x30: {'name': 'INT_SOURCE',        'element': 0, 'structure':['DATA_READY', 'SINGLE TAP', 'DOUBLE TAP', 'Activity', 'Inactivity', 'FREE_FALL', 'Watermark', 'Overrun']},
    0x31: {'name': 'DATA_FORMAT',       'element': 0, 'structure':['SELF_TEST', 'SPI 3 Wire Mode', 'Interrupt Invert', 'None' ,'Full Resolution', 'Justify Left', 'Range_1', 'Range_0']},
    0x32: {'name': 'DATAX0',            'element': 1},
    0x33: {'name': 'DATAX1',            'element': 0},
    0x34: {'name': 'DATAY0',            'element': 1},
    0x35: {'name': 'DATAY1',            'element': 0},
    0x36: {'name': 'DATAZ0',            'element': 1},
    0x37: {'name': 'DATAZ1',            'element': 0},
    0x38: {'name': 'FIFO_CTL',          'element': 0, 'structure': ['FIFO_MODE_1', 'FIFO_MODE_0', 'Triger', 'Sample_4', 'Sample_3', 'Sample_2', 'Sample_1', 'Sample_0']},
    0x39: {'name': 'FIFO_STATUS',       'element': 0, 'structure': ['FIFO_Triger', 'None', 'Entries_5', 'Entries_4', 'Entries_3', 'Entries_2', 'Entries_1', 'Entries_0']},
    0x3A: {'name': 'TAP_SIGN',          'element': 0},             # ADXL344 and ADXL346 only
    0x3B: {'name': 'ORIENT_CONF',       'element': 0},          # ADXL344 and ADXL346 only
    0x3C: {'name': 'ORIENT',            'element': 0}                # ADXL344 and ADXL346 only
}

def get_reg_name(address: int) -> str:
    try:
        return adxl_register_dict[address]['name']
    except KeyError:
        return f"0x{address:02X}"
def isSingleElement(address: int) -> bool:
    if adxl_register_dict[address]['element'] == 0:
        return True
    return False

def decode_reg(address: int, chip_reg_cnt: int, byte: int) -> str:

    string = f"0x{byte:02X} "
    try:
        register = adxl_register_dict[address + chip_reg_cnt]
        if('structure' in register):
            structure = register['structure']
            string += decode_structure(structure, byte)
        elif('scale' in register):
            string += "Value" + f"{byte * register['scale']}" + register['unit']
    except:
        string += "Fail decode"


    return string

def decode_structure(structure, byte: int) -> str:
    string = ""
    number = 0
    for i, bit_name in enumerate(structure):
        
        if(bit_name[-1].isdigit()):
            if (byte >> (7 - i) & 0b1):
                number += 0b1 << int(bit_name[-1])
            if(bit_name[-1] == '0' and number != 0):
                if string != "":
                    string += " | "
                string += bit_name[:-2] + ": " + str(number)
                number = 0
        else:
            if (byte >> (7 - i) & 0b1):
                if string != "":
                    string += " | "
                string += bit_name
    return string

        
    



class Hla(HighLevelAnalyzer):
    """ adxl Decoder """
    result_types = {
        "register": {"format": "{{data.rw}} {{data.mb}} {{data.reg_name}} : {{data.decoded}}"},
        "axis" : {"format": "{{data.reg}} : {{data.decoded}}"}
    }
    def __init__(self):
        """Initialize HLA."""
        self.n_bytes = 0
        self.start_time = 0
        self.mult_bytes = "Single Byte"
        self.first_byte = "False"
        self.reg_addr = 0
        self.reg_name = ""
        self.readwrite = "Read"

    
    def decode(self, frame: AnalyzerFrame) -> Optional[Union[Iterable[AnalyzerFrame], AnalyzerFrame]]:
        
        if frame.type == "enable":
            self.start_time = frame.start_time
            self.reg_addr = 0
            self.reg_name = ""
            self.readwrite = "Read"
            self.mult_bytes = "Single Byte"
            self.addr_wrten = False
            self.current_pos = 0
            self.concatenate = False
            return None
        elif  frame.type == "result":
            if(self.mult_bytes.lower() == "multiple bytes" and self.addr_wrten == True):
                self.reg_addr += 1
                if(self.concatenate == False):
                    self.start_time = frame.start_time
            if(self.reg_addr > 0x3D):
                self.reg_addr = 0x01    #We later retire 1
            #Datasheets says, the reserved zone is not to be accessed, not that they can not be
        elif frame.type == "disable":
            return None
        else:
            return None
        # ----------The next portion gets the FIRST Address and gets if it is a single/multiple byte read/write
        mosi = frame.data["mosi"]
        miso = frame.data["miso"]
        if self.addr_wrten == False:
            try:
                self.reg_addr = (mosi[0] & 0b00111111)
                
                self.readwrite = "Read" if ((mosi[0] >> 7) & 0b1 ==  0b1) else "Write"
                self.mult_bytes = "Multiple Bytes" if ((mosi[0] >> 6) & 0b1 == 0b1) else "Single Byte"
                self.current_pos = -1 if ((mosi[0] >> 6) & 0b1 == 0b1) else 0
                self.addr_wrten = True
            except IndexError:
                return None
            finally:
                return None
        

        # It will only arrive here in case the byte_pos is not 0, and that can only happen after the reg address has been captured 
        try:
            if self.readwrite.lower() == "write":
                byte = mosi[0]
            else:
                byte = miso[0]
        except IndexError:
                return None
        # Once we arrive here we know if the data is read or write, if only a single byte is being read or multiple, etc
        if(not isSingleElement(self.reg_addr + self.current_pos)):
            self.concatenate = True
            self.memory = byte
            return None
        if(self.concatenate == True):
            byte = (byte << 8) + self.memory
            self.concatenate = False
        self.reg_name = get_reg_name(self.reg_addr + self.current_pos)
        decoded_reg = decode_reg(self.reg_addr, self.current_pos, byte)
        return AnalyzerFrame(
            "register",
            start_time = self.start_time,
            end_time = frame.end_time,
            data = {
                "rw": self.readwrite,
                "mb": self.mult_bytes,
                "reg_name": self.reg_name,
                "decoded": decoded_reg,
            }
        )