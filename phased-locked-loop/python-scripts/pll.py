import time
import struct

# Default address of PLL board
PLL_ADDRESS                             = 0x2F
# -------- REGISTER BANK -------------
# 0x0?: SETTINGS
REGISTER_SETTINGS_DEVICE_ID             = 0x00
REGISTER_SETTINGS_HARDWARE_VERSION      = 0x01
REGISTER_SETTINGS_FIRMWARE_VERSION      = 0x02
REGISTER_SETTINGS_SAVE_TO_EEPROM        = 0x03
REGISTER_SETTINGS_PLL_REFERENCE_CLOCK   = 0x04 # 4 byte (double)
REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER = 0x06
REGISTER_SETTINGS_LED_MODE              = 0x07
REGISTER_SETTINGS_LED_BLINK_ON_TIME     = 0x08
REGISTER_SETTINGS_LED_BLINK_OFF_TIME    = 0x09

REGISTER_START_SETTINGS                 = 0x00
REGISTER_END_SETTINGS                   = 0x10

# 0x1?: PLL OPERATION
REGISTER_PLL_POWER                      = 0x10
REGISTER_PLL_FREQUENCY                  = 0x11 # 4 byte (double)
REGISTER_PLL_ENABLE_OUTPUT              = 0x13
REGISTER_PLL_LOCK_DETECTED              = 0x14 # Read only
REGISTER_PLL_MODE                       = 0x15 # Read only

REGISTER_MAP_SIZE                       = REGISTER_PLL_MODE+1
REGISTER_MAP_NR_READ_ONLY               = 2

# Register bank settings
EEPROM_STATUS_ADDRESS                   = 0
EEPROM_START_ADDRESS                    = 1
REGISTER_RESPONSE_SIZE                  = 32

# -------- VALUES CONSTANTS -----------
EEPROM_DISABLE                          = 0
EEPROM_SETTINGS                         = 1
EEPROM_ALL                              = 2

LED_MODE_OFF                            = 0
LED_MODE_ON                             = 1
LED_MODE_BLINK                          = 2
LED_MODE_PPS_BLINK                      = 3
LED_MODE_LOCK_DETECT                    = 4
LED_MODE_PPS_BLINK_AND_LOCK_DETECT      = 5

class PLL(object):
    def __init__(self, address=PLL_ADDRESS, i2c=None, **kwargs):
        if i2c is None:
            import Adafruit_GPIO.I2C as I2C
            i2c = I2C
        self._device = i2c.get_i2c_device(address, **kwargs)

        self.output = self.get_PLL_enable_output()
        self.power = self.get_PLL_power()
        self.frequency = self.get_PLL_frequency()

        self.divider = self.get_PLL_reference_divider()
        self.reference_clock = self.get_PLL_reference_clock()

    # ---- Settings -----
    # - Getters
    def get_PLL_reference_clock(self):
        result = self._device.readList(REGISTER_SETTINGS_PLL_REFERENCE_CLOCK, 4)
        return struct.unpack('f', result)[0]

    def get_PLL_reference_divider(self):
        return self._device.readU8(REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER)
        
    def get_LED_mode(self):
        return self._device.readU8(REGISTER_SETTINGS_LED_MODE)

    def get_LED_blink_on_time(self):
        return self._device.readU8(REGISTER_SETTINGS_LED_BLINK_ON_TIME)*10

    def get_LED_blink_off_time(self):
        return self._device.readU8(REGISTER_SETTINGS_LED_BLINK_OFF_TIME)*10

    # - Setters
    def set_PLL_reference_clock(self, v):
        self._device.write16(REGISTER_SETTINGS_PLL_REFERENCE_CLOCK, v)
        self.reference_clock = v
        time.sleep(0.1)

    def set_PLL_reference_divider(self, v):
        self._device.write8(REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER, v)
        self.divider = v
        time.sleep(0.1)

    def set_LED_mode(self, v):
        self._device.write8(REGISTER_SETTINGS_LED_MODE, v)

    def set_LED_blink_on_time(self, v):
        self._device.write8(REGISTER_SETTINGS_LED_BLINK_ON_TIME, v//10)

    def set_LED_blink_off_time(self, v):
        self._device.write8(REGISTER_SETTINGS_LED_BLINK_OFF_TIME, v//10)

    # ---- Operating instructions ----
    # - Getters
    def get_PLL_power(self):
        return self._device.readU8(REGISTER_PLL_POWER)

    def get_PLL_frequency(self):
        return self._device.readU16(REGISTER_PLL_FREQUENCY)

    def get_PLL_enable_output(self):
        return self._device.readU8(REGISTER_PLL_ENABLE_OUTPUT)

    def get_PLL_lock_detected(self):
        return self._device.readU8(REGISTER_PLL_LOCK_DETECTED)

    def get_PLL_mode(self):
        return self._device.readU8(REGISTER_PLL_MODE)

    # - Setters
    def set_PLL_power(self, v):
        self._device.write8(REGISTER_PLL_POWER, v)
        self.power = v
        time.sleep(0.1)

    def set_PLL_frequency(self, v):
        self._device.write16(REGISTER_PLL_FREQUENCY, v)
        self.frequency = v
        time.sleep(0.1)

    def set_PLL_enable_output(self, v):
        self._device.write8(REGISTER_PLL_ENABLE_OUTPUT, v)
        self.output = v
        time.sleep(0.1)

    # - Simpler naming functions

    def power_on(self):
        self.set_PLL_power(1)

    def power_off(self):
        self.set_PLL_power(0)

    def enable_output(self):
        self.set_PLL_enable_output(1)

    def disable_output(self):
        self.set_PLL_enable_output(0)

    def frequency(self, v):
        self.set_PLL_frequency(v)

    def locked(self):
        return self.get_PLL_lock_detected() > 0