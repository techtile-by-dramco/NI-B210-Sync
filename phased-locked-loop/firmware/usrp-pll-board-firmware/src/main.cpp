#include <Arduino.h>
#include <nI2C.h>
#include <avr/wdt.h>
#include <EEPROM.h>

#include "MAX2871.h"
#include <SPI.h>

#define DEBUG

// -------- HARDWARE PINS -------------
#define MOSI      11
#define MISO      12
#define SCLK      13
#define LE        10
#define LD        8
#define RFOUTEN   7
#define CE        9 
#define LED       6
#define PPS       2

// -------- REGISTER BANK -------------
// 0x0?: SETTINGS
#define REGISTER_SETTINGS_DEVICE_ID             0x00
#define REGISTER_SETTINGS_HARDWARE_VERSION      0x01
#define REGISTER_SETTINGS_FIRMWARE_VERSION      0x02
#define REGISTER_SETTINGS_SAVE_TO_EEPROM        0x03
#define REGISTER_SETTINGS_PLL_REFERENCE_CLOCK   0x04 // 2 byte (uint16)
#define REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER 0x06
#define REGISTER_SETTINGS_LED_MODE              0x07
#define REGISTER_SETTINGS_LED_BLINK_ON_TIME     0x08
#define REGISTER_SETTINGS_LED_BLINK_OFF_TIME    0x09

#define REGISTER_START_SETTINGS                 0x00
#define REGISTER_END_SETTINGS                   0x10

// 0x1?: PLL OPERATION
#define REGISTER_PLL_POWER                      0x10
#define REGISTER_PLL_FREQUENCY                  0x11 // 2 byte (uint16)
#define REGISTER_PLL_ENABLE_OUTPUT              0x13
#define REGISTER_PLL_LOCK_DETECTED              0x14 // Read only
#define REGISTER_PLL_MODE                       0x15 // Read only

#define REGISTER_MAP_SIZE                       REGISTER_PLL_MODE+1
#define REGISTER_MAP_NR_READ_ONLY               2

// Register bank settings
#define EEPROM_STATUS_ADDRESS                   0
#define EEPROM_START_ADDRESS                    1
#define REGISTER_RESPONSE_SIZE                  32

// -------- VALUES CONSTANTS -----------
#define EEPROM_DISABLE                          0
#define EEPROM_SETTINGS                         1
#define EEPROM_ALL                              2

#define LED_MODE_OFF                            0
#define LED_MODE_ON                             1
#define LED_MODE_BLINK                          2
#define LED_MODE_PPS_BLINK                      3
#define LED_MODE_LOCK_DETECT                    4
#define LED_MODE_PPS_BLINK_AND_LOCK_DETECT      5

// -------- DEFAULT VALUES -----------
#define SETTINGS_DEVICE_ID                      0
#define SETTINGS_HARDWARE_VERSION               0
#define SETTINGS_FIRMWARE_VERSION               0
#define SETTINGS_SAVE_TO_EEPROM                 EEPROM_SETTINGS // 0: Don't save, 1: only save settigs, 2: save complete register map
#define SETTINGS_PLL_REFERENCE_CLOCK            (double) 10.0
#define SETTINGS_PLL_REFERENCE_DIVIDER          1
#define SETTINGS_LED_MODE                       LED_MODE_BLINK // 0: Off, 1: On, 2: Blink, 3: PPS blink, 4: Lock detect, 5: Lock detect && PPS blink, PPS not implemented in V1
#define SETTINGS_LED_BLINK_ON_TIME              20 // *10 ms
#define SETTINGS_LED_BLINK_OFF_TIME             80 // *10 ms

enum address_i2c_t : byte{
    ADDRESS_I2C = 0x2F // Address of I2C device
};

// Global I2C object
CTWI i2c;

// Register map vars
uint8_t readOnlyRegisters[] = {REGISTER_PLL_LOCK_DETECTED, REGISTER_PLL_MODE};
uint8_t registerMap[REGISTER_MAP_SIZE] = {0x00};
bool registerMapUpdate = true;
bool registerMapSettingsUpdate = true;
uint8_t lastRegister = 0;

volatile bool ppsHappened = false;
uint32_t lastLedTime = 0;
uint16_t ledTimeout = 0;

// Callback function prototype
void i2cWriteCallback(const uint8_t data[], const uint8_t length);
void i2cReadCallback(void);
void readEEPROM(void);
void updateEEPROM(void);
void ppsISR(void);

// PLL Object
MAX2871 max2871(LE, MOSI, SCLK, MISO);           //create object of class MAX2871, assign latch enable pin

void setup(){
  // --- Serial setup for debugging only
#ifdef DEBUG
  Serial.begin(9600);
#endif

  // --- Setup for I2C and register map ---
  i2c.SetLocalDeviceAddress(ADDRESS_I2C);
  
  // Set read and write callback
  i2c.SetSlaveReceiveHandler(i2cWriteCallback);
  i2c.SetSlaveTransmitHandler(i2cReadCallback);

  // Load config from EEPROM
  if(EEPROM.read(EEPROM_STATUS_ADDRESS) == 1){
    readEEPROM();
  }else{
    registerMap[REGISTER_SETTINGS_DEVICE_ID] = SETTINGS_DEVICE_ID;
    registerMap[REGISTER_SETTINGS_HARDWARE_VERSION] = SETTINGS_HARDWARE_VERSION;
    registerMap[REGISTER_SETTINGS_FIRMWARE_VERSION] = SETTINGS_FIRMWARE_VERSION;
    registerMap[REGISTER_SETTINGS_SAVE_TO_EEPROM] = SETTINGS_SAVE_TO_EEPROM;
    registerMap[REGISTER_SETTINGS_PLL_REFERENCE_CLOCK] = SETTINGS_PLL_REFERENCE_CLOCK;
    registerMap[REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER] = SETTINGS_PLL_REFERENCE_DIVIDER;
    registerMap[REGISTER_SETTINGS_LED_MODE] = SETTINGS_LED_MODE;
    registerMap[REGISTER_SETTINGS_LED_BLINK_ON_TIME] = SETTINGS_LED_BLINK_ON_TIME;
    registerMap[REGISTER_SETTINGS_LED_BLINK_OFF_TIME] = SETTINGS_LED_BLINK_OFF_TIME;

    updateEEPROM();
  }

  // --- Setup for PLL ---
  // General IO setup
  pinMode(LE, OUTPUT);
  pinMode(LD, INPUT);
  pinMode(RFOUTEN, OUTPUT);
  pinMode(CE, OUTPUT);
  pinMode(MOSI, OUTPUT);
  pinMode(MISO, INPUT);
  pinMode(SCLK, OUTPUT);
  pinMode(LED, OUTPUT);
  pinMode(PPS, INPUT);

  attachInterrupt(digitalPinToInterrupt(PPS), ppsISR, RISING);

  digitalWrite(LE, HIGH);
  digitalWrite(LED, LOW);
  digitalWrite(RFOUTEN, HIGH);

  digitalWrite(CE, LOW);
  delay(100);
  digitalWrite(CE, HIGH);
  
  max2871.begin();
  //max2871.powerOn(true);              //set all hardware enable pins and deassert software shutdown bits
  //max2871.setPFD(10.0,1);             //inputs are reference frequency and R divider to set phase/frequency detector comparison frequency

#ifdef DEBUG
  Serial.println("Setup done");
#endif
}

void loop(){
  
  wdt_reset();

  // LED functions
  if(millis() - lastLedTime > ledTimeout || ppsHappened){
    if(ppsHappened){
#ifdef DEBUG
      Serial.println("PPS happened");
#endif
    }else{
#ifdef DEBUG
      Serial.print(".");
#endif
    }
    if(!digitalRead(LED)){ // LED is off, turn it on if we have to
      digitalWrite(LED, registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_ON || registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_BLINK || (ppsHappened && registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_PPS_BLINK) || (registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_LOCK_DETECT && digitalRead(LD)) || (ppsHappened && registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_PPS_BLINK_AND_LOCK_DETECT && digitalRead(LD)));
      ledTimeout = registerMap[REGISTER_SETTINGS_LED_BLINK_ON_TIME]*10;
    }else{ // LED is on, turn it off if a blink setting is selected
      digitalWrite(LED, !(registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_OFF || registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_BLINK || registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_PPS_BLINK || (registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_LOCK_DETECT && !digitalRead(LD)) || registerMap[REGISTER_SETTINGS_LED_MODE] == LED_MODE_PPS_BLINK_AND_LOCK_DETECT));
      ledTimeout = registerMap[REGISTER_SETTINGS_LED_BLINK_OFF_TIME]*10;
    }
    lastLedTime = millis();

    ppsHappened = false;
  }

  // Settings updated
  if(registerMapSettingsUpdate){
    updateEEPROM();
    uint16_t frequency = (uint16_t) ( registerMap[REGISTER_SETTINGS_PLL_REFERENCE_CLOCK] | (uint16_t)registerMap[REGISTER_SETTINGS_PLL_REFERENCE_CLOCK+1]<<8 );
    max2871.setPFD(frequency, registerMap[REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER]);
#ifdef DEBUG
    Serial.print("c:");
    Serial.println(frequency);
    Serial.print("d:");
    Serial.println(registerMap[REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER]);
#endif

    registerMapSettingsUpdate = false;
  }

  // Function registers updated
  if(registerMapUpdate){
    if(registerMap[REGISTER_SETTINGS_SAVE_TO_EEPROM] == EEPROM_ALL)
      updateEEPROM();

    if(registerMap[REGISTER_PLL_POWER] > 0){
      max2871.powerOn(true); 
    }else{
      max2871.powerOn(false);
    }

    // Repeat this, to be on the save side
    uint16_t frequency = (uint16_t) ( registerMap[REGISTER_SETTINGS_PLL_REFERENCE_CLOCK] | (uint16_t)registerMap[REGISTER_SETTINGS_PLL_REFERENCE_CLOCK+1]<<8 );
    max2871.setPFD(frequency, registerMap[REGISTER_SETTINGS_PLL_REFERENCE_DIVIDER]);

    frequency = (uint16_t) ( registerMap[REGISTER_PLL_FREQUENCY] | (uint16_t)registerMap[REGISTER_PLL_FREQUENCY+1]<<8 );
    if((frequency < 100) && (frequency > 6000)){ 
#ifdef DEBUG
        Serial.println("\n\rNot a valid frequency entry."); 
        Serial.println(frequency) ;
#endif
    }else{
      max2871.setRFOUTA((double) frequency);

      if(registerMap[REGISTER_PLL_ENABLE_OUTPUT] > 0){
        max2871.enable_output();
      }else{
        max2871.disable_output();
      }
    }
  registerMapUpdate = false;
  }

  // Set readonly registers
  registerMap[REGISTER_PLL_MODE] = max2871.getMode();
  registerMap[REGISTER_PLL_LOCK_DETECTED] = digitalRead(LD);

}

void readEEPROM(){
#ifdef DEBUG
  Serial.println("E0");
#endif

  // First read settings in temp buffer
  uint8_t registerMapTemp[REGISTER_END_SETTINGS] = {0x00};
  for(uint8_t reg = REGISTER_START_SETTINGS; reg < REGISTER_END_SETTINGS; reg++){
    registerMapTemp[reg] = EEPROM.read(reg - REGISTER_START_SETTINGS + EEPROM_START_ADDRESS);
  }

  // Now read everything according to new settings
  if(registerMapTemp[REGISTER_SETTINGS_SAVE_TO_EEPROM] != EEPROM_DISABLE){
    uint8_t end = REGISTER_END_SETTINGS;
    if(registerMapTemp[REGISTER_SETTINGS_SAVE_TO_EEPROM] == EEPROM_ALL)
      end = REGISTER_MAP_SIZE;
    for(uint8_t reg = REGISTER_START_SETTINGS; reg < end; reg++){
      registerMap[reg] = EEPROM.read(reg - REGISTER_START_SETTINGS + EEPROM_START_ADDRESS);
    }
  }
}

void updateEEPROM(){
#ifdef DEBUG
  Serial.println("E1");
#endif

  EEPROM.update(EEPROM_STATUS_ADDRESS, 1);

  if(registerMap[REGISTER_SETTINGS_SAVE_TO_EEPROM] != EEPROM_DISABLE){
    uint8_t end = REGISTER_END_SETTINGS;
    if(registerMap[REGISTER_SETTINGS_SAVE_TO_EEPROM] == EEPROM_ALL)
      end = REGISTER_MAP_SIZE;
    for(uint8_t reg = REGISTER_START_SETTINGS; reg < end; reg++){
      EEPROM.update(reg - REGISTER_START_SETTINGS + EEPROM_START_ADDRESS, registerMap[reg]);
    }
  }
}

void i2cWriteCallback(const uint8_t data[], const uint8_t length){
#ifdef DEBUG
  Serial.println("I2C write");
#endif

  if(data[0] < REGISTER_MAP_SIZE){
    // Buffer this register so we can answer to a read request later
    lastRegister = data[0];

    // If more bytes are transferred: write operation
    if(length > 1){

      // Buffer the readonly regs that can be in between
      uint8_t readOnlyTemp[REGISTER_MAP_NR_READ_ONLY];
      for(uint8_t i = 0; i < REGISTER_MAP_NR_READ_ONLY; i++){
        readOnlyTemp[i] = registerMap[readOnlyRegisters[i]];
      }
      // Copy new data
      memcpy(&registerMap[lastRegister], &data[1], length-1);
      // Put readonly back
      for(uint8_t i = 0; i < REGISTER_MAP_NR_READ_ONLY; i++){
        registerMap[readOnlyRegisters[i]] = readOnlyTemp[i];
      }
      registerMapUpdate = true;
      // Refresh EEPROM when we wrote things to settings registers
      if(lastRegister < REGISTER_END_SETTINGS || lastRegister + length < REGISTER_END_SETTINGS ){
        registerMapSettingsUpdate = true;
      }
    }
  }
}

void i2cReadCallback(void){
  // Send message to master
#ifdef DEBUG
  Serial.println("I2C read");
#endif

  uint8_t size = REGISTER_RESPONSE_SIZE; 
  if(lastRegister + REGISTER_RESPONSE_SIZE > REGISTER_MAP_SIZE){
    size = REGISTER_MAP_SIZE - lastRegister;
  } 

  i2c.SlaveQueueNonBlocking(registerMap + lastRegister, size);
}

void ppsISR(void){
  ppsHappened = true;
}

int find(uint8_t a[], uint8_t size, uint8_t item){
    int i, pos = -1;
    for (i = 0; i < size; i++) {
        if (a[i] == item) {
            pos = i;
            break;
        }
    }
    return pos;
}
