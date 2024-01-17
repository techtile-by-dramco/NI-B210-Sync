#include <Arduino.h>
// #include <stdio.h>

#include "MAX2871.h"
#include <SPI.h>

#define D6   P0_6
#define D8   P1_4
#define D9   P1_5
#define D10  P1_3
#define D11  P1_1
#define D12  P1_2
#define D13  P1_0


// SPI         spi(D11,D12,D13);           //mosi, miso, sclk
// Serial      pc(USBTX,USBRX,9600);       //tx, rx, baud

// DigitalOut  le(D10,1);                  //Latch enable pin for MAX2871
// DigitalIn   ld(D6);                     //Lock detect output pin
// DigitalOut  led(LED_BLUE,1);            //blue LED on MAX32600MBED board

// DigitalOut  rfouten(D8,1);              //RF output enable pin
// DigitalOut  ce(D9,1);                   //Chip enable pin 

#define MOSI      11
#define MISO      12
#define SCLK      13
#define LE        10
#define LD        6
#define RFOUTEN   8
#define CE        9 


double freq_entry;                  //variable to store user frequency input
char buffer[256];                   //array to hold string input from terminal

double v_tune, temperature;         //stores TUNE voltage and die temperature of MAX2871
uint32_t vco;                       //stores active VCO in use
double freq_rfouta;                 //variable to calculate ouput frequency from register settings


MAX2871 max2871(LE, MOSI, SCLK, MISO);           //create object of class MAX2871, assign latch enable pin

void setup(){

  Serial.begin(115200);
  Serial.println("Start");

  pinMode(LE, OUTPUT);
  pinMode(LD, INPUT);
  pinMode(RFOUTEN, OUTPUT);
  pinMode(CE, OUTPUT);
  // pinMode(MOSI, INPUT_PULLUP);
  pinMode(MOSI, OUTPUT);
  pinMode(MISO, INPUT);
  pinMode(SCLK, OUTPUT);

  digitalWrite(LE, HIGH);
  digitalWrite(RFOUTEN, HIGH);

  digitalWrite(CE, LOW);
  delay(100);
  digitalWrite(CE, HIGH);

  // SPI.begin();                            // Initialize SPI communication
  // SPI.setBitOrder(MSBFIRST);              // Most significant bit first
  // SPI.setDataMode(SPI_MODE0);             // Clock polarity (CPOL) = 0, Clock phase (CPHA) = 0
  // SPI.setClockDivider(SPI_CLOCK_DIV16);   // Set SPI clock to 1 MHz (16 MHz / 16)
  
  // spi.format(8,0);                     //CPOL = CPHA = 0, 8 bits per frame
  // spi.frequency(1000000);              //1 MHz SPI clock

  max2871.begin();


  max2871.powerOn(true);              //set all hardware enable pins and deassert software shutdown bits

  // Reference clock equals 10 MHz (fixed frequency by octoclocks)
  max2871.setPFD(10.0,1);             //inputs are reference frequency and R divider to set phase/frequency detector comparison frequency

}


//  The routine in the while(1) loop will ask the user to input a desired
//  output frequency, check that it is in range, calculate the corresponding
//  register settings, update the MAX2871 registers, and then independently
//  use the programmed values to re-calculate the output frequency chosen

char print_buffer [256];

void loop(){
  
  Serial.println("\nEnter a frequency in MHz\n");
  //fgets(buffer ,256, stdin);


  while(Serial.available() < 1);

  delay(100);
  
  uint8_t val = 0;

  uint32_t intValue;
  if (Serial.available() > 0) { // Check if there's data available to read
    // val ++;
    // *(buffer + val) = Serial.read(); // Read a character from the serial buffer
    // // Serial.print("Received: ");
    // Serial.println(*(buffer + val), HEX); // Print the received character

    intValue = Serial.parseInt();


    // You can add your own logic here to process the received data
  }
  
  //  Wait 10 ms
  delay(10);

  //  Flush input buffer
  while (Serial.available() > 0) {
     Serial.read();
  }

  //  Print frequency set
  Serial.println("************************************************");
  Serial.println("Frequency: " + String(intValue) + " MHz");
  
  freq_entry = intValue;                                          //convert string to a float with 1kHz precision
  if((freq_entry < 23.5) || (freq_entry > 6000.0))                //check the entered frequency is in MAX2871 range
      Serial.println("\n\rNot a valid frequency entry.");  
  else
  {
    // sprintf(print_buffer, "\n\rTarget: %.3f MHz", freq_entry);    //store entry as string until newline entered

    //Serial.println("\n\rTarget: %.3f MHz",freq_entry);   //report the frequency derived from user's input
    max2871.setRFOUTA(freq_entry);                  //update MAX2871 registers for new frequency

    uint32_t start_ms = millis();
    uint32_t timeout = 5000;
    while(!digitalRead(LD)){                                     //blink an LED while waiting for MAX2871 lock detect signal to assert
        delay(100);
        Serial.println("Waiting for lock detect");
        if(millis() > start_ms + timeout)
          break;
    }
    
    //  Enable output A
    max2871.enable_output();

    //  Print PLL mode
    Serial.println("PLL mode: " + String(max2871.getMode()));

    // !!! READING COULD CAUSE PROBLEMS !!! (TE ONDERZOEKEN)
    // vco = max2871.readVCO();                        //read the active VCO from MAX2871
    // v_tune = max2871.readADC();                     //read the digitized TUNE voltage
    // freq_rfouta = max2871.getRFOUTA();              //calculate the output frequency of channel A
    // temperature = max2871.readTEMP();               //read die temperature from MAX2871

    //print the achieved output frequency and MAX2871 diagnostics
    // Serial.println("\n\rActual: %.3f MHz", freq_rfouta);
    // sprintf(print_buffer, "\n\rActual: %.3f MHz", freq_rfouta);
    // Serial.println(print_buffer);  
    // Serial.println("\n\rVTUNE: %.3f V, VCO: %d, TEMP: %f", v_tune,vco,temperature);
    // sprintf(print_buffer, "\n\rVTUNE: %.3f V, VCO: %lu, TEMP: %f", v_tune, vco, temperature);
    // Serial.println(print_buffer);  
    // Serial.println(temperature);
    // Serial.println(v_tune);
    Serial.println("************************************************");
  }
}