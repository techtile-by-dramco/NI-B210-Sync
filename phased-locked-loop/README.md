# Techtile PLL board ✅

This PCB was developed by Guus Leenders from KU Leuven, in collaboration with DRAMCO, with assistance from Jarne Van Mulders. The board is utilized in a distributed antenna or **Radioweave** infrastructure and delivers a phase-synchronous RF output to the USRP by means of a PPS and 10MHz signal. This board is specifically designed for the USRP B210 by Ettus.

The PPS and 10MHz signals (coming from the octoclocks CDA2990) are amplified using on board buffers and are connected to the
* PLL IC (MAX287x) ❗❗ **--> allowing for ∿ phase synchronisation ∿**
* the flat cable connector (given that the raspberry pi also has access to these signals) ❗
* the input SMA connectors of the USRPs intself ❗❗ **--> ∿ frequency synchronisation ∿ internal PLLs**

The board is controlled via I2C commands and features a flat cable input connected to the RPI HAT (developed by DRAMCO) to drive the PLL output. The most important registers are displayed below.

###  PLL board general settings ⚙️

|Register name| byte |
|--|--|
|REGISTER_SETTINGS_DEVICE_ID            | 0x00 |
|REGISTER_SETTINGS_HARDWARE_VERSION     | 0x01 |
|REGISTER_SETTINGS_FIRMWARE_VERSION     | 0x02 |
|REGISTER_SETTINGS_SAVE_TO_EEPROM       | 0x03 |
|REGISTER_SETTINGS_PLL_REFERENCE_CLOCK  | 0x04 |
|REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER| 0x06 |
|REGISTER_SETTINGS_LED_MODE             | 0x07 |
|REGISTER_SETTINGS_LED_BLINK_ON_TIME    | 0x08 |
|REGISTER_SETTINGS_LED_BLINK_OFF_TIME   | 0x09 |

###  PLL (MAX287x) settings ⚙️

|Register name| byte | Remarks |
|--|--|--|
|REGISTER_PLL_POWER                     | 0x10 | |
|REGISTER_PLL_FREQUENCY                 | 0x11 | 2 byte (uint16) |
|REGISTER_PLL_ENABLE_OUTPUT             | 0x13 | |
|REGISTER_PLL_LOCK_DETECTED             | 0x14 | Read only |
|REGISTER_PLL_MODE                      | 0x15 | Read only |

# Techtile ToDo 📝
- Work further on python script To achieve phase-synchronous outputs on the oscilloscope with two separate setups consisting of RPI, USRP, PLL, PPS, and 10 MHz input.
- Current status ⏳ PENDING ⏳
