/*******************************************************************************
 * Copyright (C) 2017 Maxim Integrated Products, Inc., All Rights Reserved.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a
 * copy of this software and associated documentation files (the "Software"),
 * to deal in the Software without restriction, including without limitation
 * the rights to use, copy, modify, merge, publish, distribute, sublicense,
 * and/or sell copies of the Software, and to permit persons to whom the
 * Software is furnished to do so, subject to the following conditions:
 *
 * The above copyright notice and this permission notice shall be included
 * in all copies or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
 * OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
 * MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
 * IN NO EVENT SHALL MAXIM INTEGRATED BE LIABLE FOR ANY CLAIM, DAMAGES
 * OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
 * ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
 * OTHER DEALINGS IN THE SOFTWARE.
 *
 * Except as contained in this notice, the name of Maxim Integrated
 * Products, Inc. shall not be used except as stated in the Maxim Integrated
 * Products, Inc. Branding Policy.
 *
 * The mere transfer of this software does not imply any licenses
 * of trade secrets, proprietary technology, copyrights, patents,
 * trademarks, maskwork rights, or any other form of intellectual
 * property whatsoever. Maxim Integrated Products, Inc. retains all
 * ownership rights.
 *******************************************************************************
 */
 
 
#ifndef _MAX2871_H_
#define _MAX2871_H_


// #include "mbed.h"

#include <Arduino.h>
 
 
/** 
* @brief The MAX2871 is an ultra-wideband phase-locked loop (PLL) with integrated
* voltage control oscillators (VCOs)capable of operating in both integer-N and
* fractional-N modes. When combined with an external reference oscillator and
* loop filter, the MAX2871 is a high-performance frequency synthesizer capable
* of synthesizing frequencies from 23.5MHz to 6.0GHz while maintaining superior
* phase noise and spurious performance.
*
* @code
#include "mbed.h"
#include <stdio.h>

#include "MAX2871.h"

SPI         spi(D11,D12,D13);           //mosi, miso, sclk
Serial      pc(USBTX,USBRX,9600);       //tx, rx, baud

DigitalOut  le(D10,1);                  //latch enable
DigitalOut  ce(D9,1);                   //chip enable
DigitalOut  rfout_en(D8,1);             //RF output enable

int main() {
    float freq_entry;                   //frequency input to terminal
    float freq_actual;                  //frequency based on MAX2871 settings
    float freq_pfd;                     //frequency of phase frequency detector
    float pll_coefficient;              //fractional-N coefficient (N + F/M)
    float vco_divisor;                  //divisor from f_vco to f_rfouta
    char buffer[256];                   //string input from terminal
    
    spi.format(8,0);                    //CPOL = CPHA = 0, 8 bits per frame
    spi.frequency(1000000);             //1 MHz SPI clock

    MAX2871 max2871(spi,D10);           //create object of class MAX2871
    
    //The routine in the while(1) loop will ask the user to input a desired
    //output frequency, calculate the corresponding register settings, update
    //the MAX2871 registers, and then independently use the programmed values 
    //from the registers to re-calculate the output frequency chosen
    while(1){
        pc.printf("\n\rEnter a frequency in MHz:");
        fgets(buffer,256,stdin);        //store entry as string until newline entered
        freq_entry = atof (buffer);     //convert string to a float
        max2871.frequency(freq_entry);  //update MAX2871 registers for new frequency
        max2871.readRegister6();        //read register 6 and update max2871.reg6
        
        //Examples for how to calculate important operation parameters like
        //PFD frequency and divisor ratios using members of the MAX2871 class
        freq_pfd = max2871.f_reference*(1+max2871.reg2.bits.dbr)/(max2871.reg2.bits.r*(1+max2871.reg2.bits.rdiv2));
        pll_coefficient = (max2871.reg0.bits.n+1.0*max2871.reg0.bits.frac/max2871.reg1.bits.m);
        vco_divisor = powf(2,max2871.reg4.bits.diva);
        
        //calculate expected f_RFOUTA based on the register settings
        freq_actual = freq_pfd*pll_coefficient/vco_divisor;
        pc.printf("\n\rTarget: %.3f MHz\tActual: %.3f MHz",freq_entry,freq_actual);
        pc.printf("\n\rDie: %d, VCO: %d, F_PFD: %f",max2871.reg6.bits.die,max2871.reg6.bits.v,freq_pfd);
        pc.printf("\n\rN: %d, F: %d, M: %d, N+F/M: %f",max2871.reg0.bits.n,max2871.reg0.bits.frac,max2871.reg1.bits.m,pll_coefficient);
    }
        
}

* @endcode
*/
class MAX2871
{
public:

    //MAX2871 Registers
    enum Registers_e
    {
        REG0          = 0x00,
        REG1          = 0x01,
        REG2          = 0x02,
        REG3          = 0x03,
        REG4          = 0x04,
        REG5          = 0x05,
        REG6          = 0x06
    };
    
    //Register 0 bits
    union REG0_u
    {
        //Access all bits
        uint32_t all;
        
        //Access individual bits
        struct BitField_s
        {
            uint32_t addr       : 3;
            uint32_t frac       : 12;
            uint32_t n          : 16;
            uint32_t intfrac    : 1;
        }bits;
    };
    
    //Register 1 bits
    union REG1_u
    {
        //Access all bits
        uint32_t all;
        
        //Access individual bits
        struct BitField_s
        {
            uint32_t addr         : 3;
            uint32_t m            : 12;
            uint32_t p            : 12;
            uint32_t cpt          : 2;
            uint32_t cpl          : 2;
            uint32_t reserved1    : 1;
        }bits;
    };
    
    //Register 2 bits
    union REG2_u
    {
        //Access all bits
        uint32_t all;
        
        //Access individual bits
        struct BitField_s
        {
            uint32_t addr      : 3;
            uint32_t rst       : 1;
            uint32_t tri       : 1;
            uint32_t shdn      : 1;
            uint32_t pdp       : 1;
            uint32_t ldp       : 1;
            uint32_t ldf       : 1;
            uint32_t cp        : 4;
            uint32_t reg4db    : 1;
            uint32_t r         : 10;
            uint32_t rdiv2     : 1;
            uint32_t dbr       : 1;
            uint32_t mux       : 3;
            uint32_t sdn       : 2;
            uint32_t lds       : 1;
        }bits;
    };
    
    //Register 3 bits
    union REG3_u
    {
        //Access all bits
        uint32_t all;
        
        //Access individual bits
        struct BitField_s
        {
            uint32_t addr      : 3;
            uint32_t cdiv      : 12;
            uint32_t cdm       : 2;
            uint32_t mutedel   : 1;
            uint32_t csm       : 1;
            uint32_t reserved1 : 5;
            uint32_t vas_temp  : 1;
            uint32_t vas_shdn  : 1;
            uint32_t vco       : 6;
        }bits;
    };
    
    //Register 4 bits
    union REG4_u
    {
        //Access all bits
        uint32_t all;
        
        //Access individual bits
        struct BitField_s
        {
            uint32_t addr       : 3;
            uint32_t apwr       : 2;
            uint32_t rfa_en     : 1;
            uint32_t bpwr       : 2;
            uint32_t rfb_en     : 1;
            uint32_t bdiv       : 1;
            uint32_t mtld       : 1;
            uint32_t sdvco      : 1;
            uint32_t bs         : 8;
            uint32_t diva       : 3;
            uint32_t fb         : 1; //1
            uint32_t bs2        : 2;
            uint32_t sdref      : 1;
            uint32_t sddiv      : 1;
            uint32_t sdldo      : 1;
            uint32_t reservered1: 3;
        }bits;
    };
    
    //Register 5 bits
    union REG5_u
    {
        //Access all bits
        uint32_t all;
        
        //Access individual bits
        struct BitField_s
        {
            uint32_t addr      : 3;
            uint32_t adcm      : 3;
            uint32_t adcs      : 1;
            uint32_t reserved1 : 11;
            uint32_t mux       : 1;
            uint32_t reserved2 : 3;
            uint32_t ld        : 2;
            uint32_t f01       : 1;
            uint32_t sdpll     : 1;
            uint32_t reserved3 : 3;
            uint32_t vas_dly   : 2;
            uint32_t reserved4 : 1;
            
        }bits;
    };
    
    //Register 6 bits
    union REG6_u
    {
        //Access all bits
        uint32_t all;
        
        //Access individual bits
        struct BitField_s
        {
            uint32_t addr      : 3;
            uint32_t v         : 6;
            uint32_t vasa      : 1;
            uint32_t reserved1 : 5;
            uint32_t adcv      : 1;
            uint32_t adc       : 7;
            uint32_t por       : 1;
            uint32_t reserved2 : 4;
            uint32_t die       : 4;
        }bits;
    };
    
    ///@brief MAX2871 Constructor
    ///@param spiBus - Reference to spi interface
    ///@param le - Pin used for latch enable
    MAX2871(uint8_t le, uint8_t mosi, uint8_t sclk, uint8_t miso);

    void begin();
    
    ///@brief MAX2871 Destructor
    // ~MAX2871();
       
    ///@brief Writes raw 32-bit data pattern. The MAX2871 accepts 32-bit words at a time; 29 data bits and 3 address bits.
    ///
    ///On Entry:
    ///@param[in] data - 32-bit word to write to the MAX2871. Bits[31:3] contain the register data, and Bits[2:0] contain the register address.
    ///
    ///@returns None
    void write(const uint32_t data);
    
    ///@brief Read Register 6 and update reg6 member variable. The MAX2871 only has one readable register - Register 6.
    ///
    ///@returns 32-bit word whose lowest bits are '110' indicating register address 6.
    uint32_t readRegister6();
    
    ///@brief Updates MAX2871 settings to achieve target output frequency on channel A.\n
    ///
    ///On Entry:
    ///@param[in] freq - Frequency in MHz 
    ///
    ///@returns None
    void setRFOUTA(const double freq);
    
    ///@brief Provide frequency input to REF_IN pin.\n
    ///
    ///On Entry:
    ///@param[in] ref_in - Frequency in MHz
    ///
    ///@returns None
    void setPFD(const double ref_in, const uint16_t rdiv);
    
    double getPFD();
    
    ///@brief Read ADC voltage.\n
    ///
    ///On Entry:
    ///
    ///@returns ADC reading in Volts   
    double readADC();
    
    uint32_t readVCO();
    
    void powerOn(const bool pwr);
    
    double getRFOUTA();
    
    double readTEMP();
    
    void updateAll();

    uint8_t getMode();

    void disable_output();
    void enable_output();

private:

    // SPI &m_spiBus;
    uint8_t m_le;
    uint8_t m_mosi;
    uint8_t m_sclk;
    uint8_t m_miso;
    
    REG0_u reg0;
    REG1_u reg1;
    REG2_u reg2;
    REG3_u reg3;
    REG4_u reg4;
    REG5_u reg5;
    REG6_u reg6;
    
    double f_pfd;
    double f_rfouta;
};
 
#endif /* _MAX2871_H_ */
 