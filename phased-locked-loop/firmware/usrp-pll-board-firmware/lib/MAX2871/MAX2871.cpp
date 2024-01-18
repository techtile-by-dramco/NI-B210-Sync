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
 
 
#include "MAX2871.h"
// #include <math.h>
#include <stdio.h>
// #include <SPI.h>

double myRound(double number);
 
//****************************************************************************
MAX2871::MAX2871(uint8_t le, uint8_t mosi, uint8_t sclk, uint8_t miso){
// m_spiBus(spiBus), m_le(le, 1)
    m_le = le;
    m_mosi = mosi;
    m_sclk = sclk;
    m_miso = miso;
}


//****************************************************************************
void MAX2871::begin(){
    reg0.all = 0x007d0000;
    reg1.all = 0x2000fff9;
    reg2.all = 0x00004042;
    reg3.all = 0x0000000b;
    reg4.all = 0x6180b23c;
    reg5.all = 0x00400005;
    reg6.all = 0x00000000;

    // reg4.bits.fb = 0;
    
    updateAll();
    
    delay(20);
    
    updateAll();
}

// //****************************************************************************
// MAX2871::~MAX2871()
// {
//     //empty block
// }

//****************************************************************************    
void MAX2871::write(const uint32_t data)
{
    // m_le = 0;
    // digitalWrite(m_le, LOW);
    // SPI.transfer((0xFF000000 & data) >> 24);
    // SPI.transfer((0x00FF0000 & data) >> 16);
    // SPI.transfer((0x0000FF00 & data) >> 8);
    // SPI.transfer( 0x000000FF & data);
    // digitalWrite(m_le, HIGH);
    // m_le = 1;

    digitalWrite(m_le, LOW);

    shiftOut(m_mosi, m_sclk, MSBFIRST, ((data & 0xFF000000) >> 24));
    shiftOut(m_mosi, m_sclk, MSBFIRST, ((data & 0x00FF0000) >> 16));
    shiftOut(m_mosi, m_sclk, MSBFIRST, ((data & 0x0000FF00) >> 8));
    shiftOut(m_mosi, m_sclk, MSBFIRST, (data & 0x000000FF));

    digitalWrite(m_le, HIGH);
}

//****************************************************************************    
void MAX2871::updateAll()
{
    write(reg5.all);
    write(reg4.all);
    write(reg3.all);
    write(reg2.all);
    write(reg1.all);
    write(reg0.all);
}

//****************************************************************************    
uint32_t MAX2871::readRegister6()
{
    uint32_t raw, reg6read;
    
    reg5.bits.mux = 1;
    reg2.bits.mux = 0x4;
    write(reg5.all);
    write(reg2.all);
    
    write(0x00000006);
    
    // m_spiBus.format(8,1);
    // SPI.setDataMode(SPI_MODE3);
    
    // raw = SPI.transfer(0x00);
    raw = shiftIn(m_miso, m_sclk, MSBFIRST); 
    reg6read = (reg6read & 0x01FFFFF) + (raw << 25);
    // raw = SPI.transfer(0x00);
    raw = shiftIn(m_miso, m_sclk, MSBFIRST); 
    reg6read = (reg6read & 0xFE01FFFF) + (raw << 17); 
    // raw = SPI.transfer(0x00);
    raw = shiftIn(m_miso, m_sclk, MSBFIRST); 
    reg6read = (reg6read & 0xFFFE01FF) + (raw << 9);
    // raw = SPI.transfer(0x00);
    raw = shiftIn(m_miso, m_sclk, MSBFIRST); 
    reg6read = (reg6read & 0xFFFFFE01) + (raw << 1);
    
    // SPI.transfer(0x00);
    shiftOut(m_mosi, m_sclk, MSBFIRST, 0x00); 
    
    // m_spiBus.format(8,0);
    // SPI.setDataMode(SPI_MODE0);
    
    return reg6read;
}

double myRound(double number) {
  return (number < 0.0) ? ceil(number - 0.5) : floor(number + 0.5);
}

//****************************************************************************    
void MAX2871::setRFOUTA(const double freq)
{
    uint32_t n,frac,m,diva = 0;
    double pll_coefficient,fractional = 0;
    
    double f_pfd = getPFD();
    
    while(freq*powf(2,diva) < 3000.0)
    {
        diva = diva + 1;
    }
    pll_coefficient = freq*powf(2,diva)/f_pfd;

    n = floor(round(pll_coefficient));
    // n = static_cast<uint32_t>(round(pll_coefficient));
    
    fractional = pll_coefficient - n;

    if(fractional < 0){
        fractional = 0;
    }

    m = 4000;
    // frac = rint(m*fractional);
    frac = myRound(m*fractional);

    // Serial.println("Frac: " + String(frac) + " | n: " + String(n) + " | m: " + String(m) + " | diva: " + String(diva));

        // My code (Jarne Van Mulders)
    if(frac == 0){
        reg0.bits.intfrac = 1;
        reg4.bits.fb = 0;
        reg2.bits.ldf = 1;
        reg1.bits.cpl = 0x00;

        n = n / powf(2, diva);
    }
    
    reg0.bits.frac = frac;
    reg0.bits.n = n;
    reg1.bits.m = m;
    reg4.bits.diva = diva;

#ifdef DEBUG
    Serial.println("Frac: " + String(frac) + " | n: " + String(n) + " | m: " + String(m) + " | diva: " + String(diva));
#endif
    reg3.bits.mutedel = 1;
    
    updateAll();
    f_rfouta = f_pfd*(reg0.bits.n+1.0*reg0.bits.frac/reg1.bits.m)/powf(2,reg4.bits.diva);
}

void MAX2871::setPFD(const double ref_in,const uint16_t rdiv)
{
    f_pfd = ref_in/rdiv;//*2;

    // x2
    //reg2.bits.dbr = 1;
    
    if(f_pfd > 32.0)
        reg2.bits.lds = 1;
    else reg2.bits.lds = 0;
    
    reg3.bits.cdiv = myRound(f_pfd/0.10);
    
    reg2.bits.dbr = 0;
    reg2.bits.rdiv2 = 0;
    reg2.bits.r = rdiv;
    
    uint32_t bs = f_pfd*20;
    
    if (bs > 1023)
        bs = 1023;
    else if (bs < 1)
        bs = 1;
        
    reg4.bits.bs = 0x03FF & bs;
    reg4.bits.bs2 = 0x03 & (bs >> 8);

    reg4.bits.rfa_en = 0;
    reg4.bits.rfb_en = 0;

    // my code
    // reg2.bits.sdn = 0x00;
    // reg4.bits.apwr = 0x03;

    // My code (Jarne Van Mulders)
    // Disable phase shifts
    // reg3.bits.cdm = 0;
    // // Value p = 0
    // reg1.bits.p = 2000;
    
    updateAll();
}

double MAX2871::readADC()
{   
    reg5.bits.adcm = 0x4;
    reg5.bits.adcs = 1;
    write(reg5.all);
    delayMicroseconds(100);
    
    reg6.all = readRegister6();
    
    reg5.bits.adcm = 0;
    reg5.bits.adcs = 0;
    write(reg5.all);
    
    if((reg6.bits.vasa == 0) & (reg6.bits.adcv = 1))
    {
        double volts = 0.315 + 0.0165*(double)reg6.bits.adc; 
        return volts;
    } else
        return -1;
}

uint32_t MAX2871::readVCO()
{

    reg6.all = readRegister6();
    
    return reg6.bits.v;
}

void MAX2871::powerOn(const bool pwr)
{
    reg2.bits.shdn =  !pwr;
    reg4.bits.sdldo = !pwr;
    reg4.bits.sddiv = !pwr;
    reg4.bits.sdref = !pwr;
    reg4.bits.sdvco = !pwr;
    reg5.bits.sdpll = !pwr;
        
    updateAll();
}

double MAX2871::getPFD()
{
    return f_pfd;
}

double MAX2871::getRFOUTA()
{
    f_rfouta = f_pfd*(reg0.bits.n+1.0*reg0.bits.frac/reg1.bits.m)/powf(2,reg4.bits.diva);
    return f_rfouta;
}

double MAX2871::readTEMP()
{   
    reg5.bits.adcm = 0x1;
    reg5.bits.adcs = 1;
    write(reg5.all);
    delayMicroseconds(100);
    
    reg6.all = readRegister6();
    
    reg5.bits.adcm = 0;
    reg5.bits.adcs = 0;
    write(reg5.all);
    
    if(reg6.bits.adcv == 1)
    {
        double degrees = 95 - 1.14*(double)reg6.bits.adc; 
        return degrees;
    } else
        return -1;
}

uint8_t MAX2871::getMode(){
    return reg0.bits.intfrac;
}

void MAX2871::disable_output(){
    reg4.bits.rfa_en = 0;
    reg4.bits.rfb_en = 0;
    updateAll();
}

void MAX2871::enable_output(){
    reg4.bits.rfa_en = 1;
    reg4.bits.rfb_en = 0;
    
    updateAll(); 
}