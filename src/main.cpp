/*
 * On-Instrument Slide Temperature Measurement System
 * Description: Firmware designed to run on a 
 * Teensy 4.1 Microcontroller (Arduino Based). Commands a 
 * TI - ADS124S08 ADS to measure 6 thermistors, process all 
 * raw sensor data and report telemetry to a host computer 
 * via USB serial in intervals ≤ 3 seconds. 
 * Date: 22 Jan 2024
 */
#include "ADS124S08.h"
#include <time.h>
#include <Math.h>

//#define WIRE4
#define THERMISTOR
#define THERMISTORNOMINAL 10000
#define BCOEFFICIENT 2.532850634e-4// 3948 B value for 40/100C, 2.5316447e-4, 3950 B value for 25/100C
#define TEMPERATURENOMINAL 298.15   // 25 C
#define VS 2.5                      // Source Voltage = 2.5V
#define R_DIVIDER 10000
#define ADC_FULLSCALE 8388608       // (ADC_fullscale = 2^23 * PGA_Value) = 2^23 * 1 for thermistor

#define A_REF 1.032e-3
#define B_REF 2.387e-4
#define C_REF 1.580e-7

ADS124S08 adc;
// ADS124S08 adc2;
// ADS124S08 adc3;

uint8_t statusOld = -1;
long lastSample[6];
int counter;
int sampleNumber = 1;
int lastButtonStatus = 0;
int useIDAC = 0;

String output;

struct adc_inputs {
  String thermistorNum;
  uint8_t AIN_P;
  uint8_t AIN_N;
  bool isRef;
};

struct adc_inputs adc_in[] = 
{
  {"Ref", ADS_P_AIN1, ADS_N_AIN9, true},    // Ref Sensor
  {"T1", ADS_P_AIN0, ADS_N_AIN9, false},   // thermistor1
  {"T2", ADS_P_AIN2, ADS_N_AIN9, false},   // thermistor2
  {"T3", ADS_P_AIN1, ADS_N_AIN9, false},   // thermistor3
  {"T4", ADS_P_AIN6, ADS_N_AIN9, false},   // thermistor4
  {"T5", ADS_P_AIN8, ADS_N_AIN9, false},   // thermistor5
  {"T6", ADS_P_AIN10, ADS_N_AIN9, false}  // thermistor6
};

void regMap2(void)
{
	unsigned int index;
	uint8_t cTemp[18];
  adc.readRegs(0,18,cTemp);
  Serial.println("Register Contents");
	Serial.println("---------------------");

	for(index=0; index < 18 ; index++)
	{
		Serial.printf("Register 0x%02x = 0x%02x\n", index, cTemp[index] );
	}
}

void configureAdc_thermistor(uint8_t P_AIN, uint8_t N_AIN)
{
  // Make sure the device is awake
  adc.sendCommand( WAKE_OPCODE_MASK );
  // adc.regWrite( DATARATE_ADDR_MASK, 0x34);
  // use channel 8 as positive and channel 9 as negative input
  adc.regWrite( INPMUX_ADDR_MASK, P_AIN + N_AIN);
  // set PGA to Bypass
  adc.regWrite( PGA_ADDR_MASK, ADS_PGA_BYPASS );
  // The IDAC will only work if we enable the internal reference (ref Datasheet 9.3.7)
  adc.regWrite( REF_ADDR_MASK, ADS_REFINT_ON_ALWAYS + ADS_REFSEL_P0 );
  // use channel 3 as IDAC 1 (excitation current source)
  adc.regWrite( IDACMUX_ADDR_MASK, ADS_IDAC1_OFF + ADS_IDAC2_OFF );
  // set IDAC 1 off 
  adc.regWrite( IDACMAG_ADDR_MASK, ADS_IDACMAG_OFF);
  // Turn on status for debugging
  adc.regWrite( SYS_ADDR_MASK, ADS_SENDSTATUS_ENABLE );

  //adc.regWrite( DATARATE_ADDR_MASK, 0x34);

  adc.reStart();
  delay(50);

  // adc.sendCommand( RDATA_OPCODE_MASK );
  // delay(50);

  //regMap2();
}


float getCelcius( float thermistance )
 {
    //Serial.print("Celsius1: R = ");Serial.println(thermistance);
    float temp_C = (1/((1/TEMPERATURENOMINAL) + BCOEFFICIENT*log(thermistance/THERMISTORNOMINAL))) - 273.15;   // Convert thermistance to temperature
    return temp_C;
 }

float getCelcius2(float thermistance)
{
  //Serial.print("Celsius2: R = ");Serial.println(thermistance);
  float temp_C = (1 / (A_REF + (B_REF * log(thermistance)) + (C_REF * pow(log(thermistance), 3)))) - 273.15;
  return temp_C;
}

uint8_t readData(ADS124S08 adc, bool isRef)
{
	uint8_t dStatus = 0;
	uint8_t dData;
	uint8_t dCRC = 0;
	int data = 0;

	/* Read out the results  */
	data = adc.dataRead(&dStatus, &dData, &dCRC);
	/*
	 * Need to determine if Status and/or CRC is enabled to transmit as desired
	 */
	if((adc.registers[SYS_ADDR_MASK] & 0x01) == DATA_MODE_STATUS)
  {
		if((adc.registers[SYS_ADDR_MASK] & 0x02) == DATA_MODE_CRC)
		{
			//Serial.printf("Conversion Data 0x%06x with Status 0x%02x and CRC 0x%02x.\n", data, dStatus, dCRC);
		}
		else
    {
      //Serial.printf("Conversion Data 0x%06x with Status 0x%02x. DEC %02d\n", data, dStatus,data);
    }
  }
	else if((adc.registers[SYS_ADDR_MASK] & 0x02) == DATA_MODE_CRC)
	{
		//Serial.printf("Conversion Data 0x%06x with CRC 0x%02x.\n", data, dCRC);
	}
	else
  {
    //Serial.printf("Conversion Data 0x%06x.\n", data);
  }

  float voltage_RT = (float(data) / ADC_FULLSCALE) * VS;
  float thermistance = R_DIVIDER * (1 / ((VS/voltage_RT) - 1));

  // Serial.print("Voltage: ");
  // Serial.println(voltage, 6);
  // Serial.print("Thermistance: ");
  // Serial.println(thermistance);
  float temp;
  if(isRef)
  {
    temp = getCelcius2(thermistance);
  }
  else 
  {
    temp = getCelcius(thermistance);
  }
  output.append(String(temp,2) + " °C " + String(thermistance,2) + "-");

	/* Set ADC back to the previous configuration */
	//adc.sendCommand(STOP_OPCODE_MASK);
	//adc.sendCommand(SLEEP_OPCODE_MASK);

  return dStatus;
}

void regMap(ADS124S08 adc)
{
	unsigned int index;
	char cTemp;
	Serial.println("Register Contents");
	Serial.println("---------------------");
	for(index=0; index < 18 ; index++)
	{
		cTemp = adc.regRead(index);
		Serial.printf("Register 0x%02x = 0x%02x\n", index, cTemp);
	}
}

#define bitRead(value, bit) (((value) >> (bit)) & 0x01)
#define bitSet(value, bit) ((value) |= (1UL << (bit)))
#define bitClear(value, bit) ((value) &= ~(1UL << (bit)))
 // #define bitWrite(value, bit, bitvalue) (bitvalue ? bitSet(value, bit) : bitClear(value, bit)) // Defined in wiring.h


// setup() runs once, when the device is first turned on.
void setup() {
  Serial.begin(9600);

  // ADC 1 Init
  delay(3000);
  adc.begin();
  delay(100);
  adc.sendCommand(RESET_OPCODE_MASK);
  delay(100);

  /* print out the chip name */
  while(adc.regRead(STATUS_ADDR_MASK) != 0x80)
  {
    Serial.println("ADC 1 not found.Retrying in 5 seconds");
    delay(5000);
  }
  if( adc.regRead(ID_ADDR_MASK) == 0x00 )
  {
    Serial.println("ADC 1 found.");
    adc.regWrite(STATUS_ADDR_MASK, 0x00);
  }
  delay(10);
  #ifdef WIRE4

  #else
    configureAdc_thermistor(adc_in[0].AIN_P, adc_in[0].AIN_N); // Start on thermistor 1
    delay(100);
  #endif
}


void loop() {
  long now = millis();
  uint8_t status;
  int channel;

  output="";

  for(channel = 0; channel < 1; channel++)
  {
      // Check if it's X seconds since last conversion
      if( now - lastSample[channel] > 50 ){

        configureAdc_thermistor(adc_in[channel].AIN_P, adc_in[channel].AIN_N);
   
        output.append(adc_in[channel].thermistorNum + " ");

        status = readData(adc, adc_in[channel].isRef);

        uint8_t rdy    = bitRead(status, 6);
        uint8_t por    = bitRead(status, 7);
        if(statusOld != status )
        {
          statusOld = status;
          Serial.print("status: ");
          Serial.print( status,BIN );
          Serial.print(" POR: ");
          Serial.print( bitRead(status, 7) );
          Serial.print(" RDY: ");
          Serial.println( rdy );

          // the chip restarted (for some reason) so clear the POR flag, but only when ready
          if( por == 1 && rdy == 0){
            // clear the POR flag and reconfigure
            bitWrite(status, 7, 0);
            adc.regWrite(STATUS_ADDR_MASK, status);
            configureAdc_thermistor(adc_in[channel].AIN_P, adc_in[channel].AIN_N);
            // print debug info so we can see if this worked
            status = adc.regRead( STATUS_ADDR_MASK );
            Serial.print( "POR cleared? " );
            Serial.println(status,BIN);
          }
        }
        delay(50);
      }
  }
  Serial.println(output);
  sampleNumber++;
}
