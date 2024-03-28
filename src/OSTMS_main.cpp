/*
 * Project: On-Instrument Slide Temperature Measurement System
 *
 * Description: 
 * This firmware is specifically designed to run on a Teensy 4.1 Microcontroller, 
 * leveraging the capabilities of a TI ADS124S08 Analog-to-Digital Converter (ADC) to measure 
 * temperatures from 6 thermistors. It processes raw sensor data to compute temperature readings 
 * and reports the telemetry to a host computer via USB serial within intervals of 3 seconds or less. 
 * The firmware's efficient design ensures rapid data acquisition and processing, suitable for high-precision 
 * temperature monitoring applications.
 *
 * Key Features:
 * - Utilizes the TI ADS124S08 ADC for high-precision measurements.
 * - Supports up to 6 thermistors for comprehensive temperature monitoring.
 * - Delivers temperature data to the host computer in 3 seconds or less.
 * - Designed for the Teensy 4.1 Microcontroller for optimal performance and compatibility.
 *
 * Version: 1.0
 * Author: Nestor Garcia
 * Date: 14 Feb 2024
 * License: [Specify License]
 * 
 * Instructions for Use:
 * 1. Ensure the Teensy 4.1 Microcontroller is properly connected and set up.
 * 2. Connect the TI ADS124S08 ADC and thermistors according to the system schematics.
 * 3. Compile and upload this firmware to the Teensy 4.1 Microcontroller.
 * 4. Run the host computer software to begin receiving temperature telemetry.
 *
 * Note: This firmware is part of a collaborative project. Please ensure proper calibration of the 
 * thermistors and ADC for accurate temperature measurements.
 */

#include "ADS124S08.h"
#include <time.h>
#include <Math.h>
#include <ArduinoJson.h>

 float ohmTable[501] = {100,100.39,100.78,101.17,101.56,101.95,102.34,102.73,103.12,
 103.51,103.9,104.29,104.68,105.07,105.46,105.85,106.24,106.63,107.02,107.4,107.79,
 108.18,108.57,108.96,109.35,109.73,110.12,110.51,110.9,111.28,111.67,112.06,112.45,
 112.83,113.22,113.61,113.99,114.38,114.77,115.15,115.54,115.93,116.31,116.7,117.08,
 117.47,117.85,118.24,118.62,119.01,119.4,119.78,120.16,120.55,120.93,121.32,121.7,
 122.09,122.47,122.86,123.24,123.62,124.01,124.39,124.77,125.17,125.55,125.93,126.32,
 126.7,127.08,127.46,127.85,128.23,128.61,128.99,129.38,129.76,130.14,130.52,130.9,
 131.28,131.67,132.05,132.43,132.81,133.19,133.57,133.95,134.33,134.71,135.09,135.47,
 135.85,136.23,136.61,136.99,137.37,137.75,138.13,138.51,138.89,139.27,139.65,140.03,
 140.39,140.77,141.15,141.53,141.91,142.29,142.66,143.04,143.42,143.8,144.18,144.56,
 144.94,145.32,145.69,146.07,146.45,146.82,147.2,147.58,147.95,148.33,148.71,149.08,
 149.46,149.83,150.21,150.58,150.96,151.34,151.71,152.09,152.46,152.84,153.21,153.58,
 153.95,154.32,154.71,155.08,155.46,155.83,156.21,156.58,156.96,157.33,157.71,158.08,
 158.45,158.83,159.2,159.56,159.94,160.31,160.68,161.05,161.43,161.8,162.17,162.54,
 162.91,163.28,163.66,164.03,164.4,164.77,165.14,165.51,165.88,166.25,166.62,167,
 167.37,167.74,168.11,168.48,168.85,169.22,169.59,169.96,170.33,170.69,171.06,
 171.43,171.8,172.17,172.54,172.91,173.27,173.64,174.01,174.39,174.75,175.12,
 175.49,175.86,176.23,176.59,176.96,177.33,177.7,178.06,178.43,178.8,179.16,179.53,
 179.9,180.26,180.63,180.99,181.36,181.73,182.09,182.46,182.82,183.19,183.55,183.92,
 184.28,184.65,185.01,185.38,185.74,186.11,186.47,186.84,187.2,187.56,187.93,188.29,
 188.65,189.02,189.38,189.74,190.11,190.47,190.83,191.2,191.56,191.92,192.28,192.66,
 193.02,193.38,193.74,194.1,194.47,194.83,195.19,195.55,195.9,196.26,196.62,196.98,
 197.35,197.71,198.07,198.43,198.79,199.15,199.51,199.87,200.23,200.59,200.95,201.31,
 201.67,202.03,202.38,202.74,203.1,203.46,203.82,204.18,204.54,204.9,205.25,205.61,
 205.97,206.33,206.7,207.05,207.41,207.77,208.13,208.48,208.84,209.2,209.55,209.91,
 210.27,210.62,210.98,211.34,211.69,212.05,212.4,212.76,213.12,213.47,213.83,214.19,
 214.55,214.9,215.26,215.61,215.97,216.32,216.68,217.03,217.39,217.73,218.08,218.44,
 218.79,219.15,219.5,219.85,220.21,220.56,220.91,221.27,221.62,221.97,222.32,222.68,
 223.03,223.38,223.73,224.09,224.45,224.8,225.15,225.5,225.85,226.21,226.56,226.91,
 227.26,227.61,227.96,228.31,228.66,229.01,229.36,229.72,230.07,230.42,230.77,231.12,
 231.47,231.81,232.16,232.51,232.86,233.21,233.56,233.91,234.26,234.6,234.95,235.3,
 235.65,236,236.35,236.7,237.05,237.4,237.75,238.09,238.44,238.79,239.14,239.48,239.83,
 240.18,240.52,240.87,241.22,241.56,241.91,242.25,242.6,242.95,243.29,243.64,243.98,
 244.33,244.67,245.02,245.36,245.71,246.05,246.4,246.74,247.09,247.43,247.78,248.12,
 248.46,248.81,249.15,249.5,249.84,250.18,250.53,250.89,251.21,251.55,251.9,252.24,
 252.59,252.94,253.28,253.62,253.96,254.3,254.65,254.99,255.33,255.67,256.01,256.35,
 256.7,257.04,257.38,257.72,258.06,258.4,258.74,259.08,259.42,259.76,260.1,260.44,
 260.78,261.12,261.46,261.8,262.14,262.48,262.83,263.17,263.5,263.84,264.18,264.52,
 264.86,265.2,265.54,265.87,266.21,266.55,266.89,267.22,267.56,267.9,268.24,268.57,
 268.91,269.25,269.58,269.92,270.26,270.59,270.93,271.27,271.6,271.94,272.27,272.61,
 272.95,273.28,273.62,273.95,274.29,274.62,274.96,275.29,275.63,275.96,276.31,276.64,
 276.97,277.31,277.64,277.98,278.31,278.64,278.98,279.31,279.64,279.98,280.31,280.64,280.98};

#define THERMISTOR
#define THERMISTORNOMINAL 10000
//#define BCOEFFICIENT 2.532850634e-4// ametherm: 3948 B value for 40/100C, 2.5316447e-4, 3950 B value for 25/100C
#define BCOEFFICIENT 2.896032436e-4// tdk: 3380 B value for 40/100C, 2.5316447e-4, 3453 B value for 25/100C
#define TEMPERATURENOMINAL 298.15   // 25 C
#define VS 2.5                      // Source Voltage = 2.5V
#define R_DIVIDER 10000
#define ADC_FULLSCALE 8388608       // (ADC_fullscale = 2^23 * PGA_Value) = 2^23 * 1 for thermistor
//#define ADC_FULLSCALE 16777216
#define A_REF 1.032e-3
#define B_REF 2.387e-4
#define C_REF 1.580e-7

#define NUM_THERMISTORS 6

static bool refOn = false;

bool handleConversion();
void adsReady_1();

//  two interrupt flags
static bool RDY_1 = false;
uint8_t channel_1 = 0;         //  thermistor to read
uint8_t dStatus = 0;

//  array to hold the data. 
float temps[7] = { 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0};
JsonDocument tsaDoc;
JsonDocument messageDoc;

ADS124S08 adc;

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
  {"T1", ADS_P_AIN0, ADS_N_AIN9, false},   // thermistor1
  {"T2", ADS_P_AIN2, ADS_N_AIN9, false},   // thermistor2
  {"T3", ADS_P_AIN6, ADS_N_AIN9, false},   // thermistor3
  {"T4", ADS_P_AIN4, ADS_N_AIN9, false},   // thermistor4
  {"T5", ADS_P_AIN8, ADS_N_AIN9, false},   // thermistor5
  {"T6", ADS_P_AIN10, ADS_N_AIN9, false},  // thermistor6
  {"Ref", ADS_P_AIN1, ADS_N_AIN9, true}    // Ref Sensor
};

void regMap2(void)
{
	unsigned int index;
	uint8_t cTemp[18];
  adc.readRegs(0,18,cTemp);
  messageDoc["type"] = "Info";
  messageDoc["message"] = "Register Contents";
  serializeJson(messageDoc, Serial);
  Serial.println();

	for(index=0; index < 18 ; index++)
	{
    messageDoc["type"] = "Info";
    messageDoc["message"] = "Register 0x%02x = 0x%02x\n", index, cTemp[index] ;
    serializeJson(messageDoc, Serial);
    Serial.println();		
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

  adc.regWrite( DATARATE_ADDR_MASK, ADS_CONVMODE_SS + ADS_FILTERTYPE_LL + ADS_DR_20);

  adc.sendCommand(START_OPCODE_MASK);
  delay(50);
}

// Main thermistor function
float getCelcius( float thermistance )
 {
    float temp_C = (1/((1/TEMPERATURENOMINAL) + BCOEFFICIENT*log(thermistance/THERMISTORNOMINAL))) - 273.15;   // Convert thermistance to temperature
    temps[channel_1] = temp_C;
    return temp_C;
 }

// For thermistor reference
float getCelcius2(float thermistance)
{
  float temp_C = (1 / (A_REF + (B_REF * log(thermistance)) + (C_REF * pow(log(thermistance), 3)))) - 273.15;
  temps[6] = temp_C;
  return temp_C;
}

// For rtd reference
float getCelcius3( float ohmMeasured )
 {
   float below, above, interpol;
   int i;
   for( i=0; i<501; i++ )
   {
     if( ohmMeasured < ohmTable[i] )
     {
       above = ohmTable[i];
       below = ohmTable[i-1];
       break;
     }
   }
   float range = above-below;
   float remain = ohmMeasured-below;
   float percent = (remain / range);
   interpol = i - 1 + percent;
   temps[6] = interpol;
   return interpol;
 }

float readData(ADS124S08 adc, bool isRef)
{
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

  if(isRef)
  {
    getCelcius2(thermistance);
  }
  else 
  {
    getCelcius(thermistance);
  }
  return dStatus;
}

void regMap(ADS124S08 adc)
{
	unsigned int index;
	char cTemp;
  messageDoc["type"] = "Info";
  messageDoc["message"] = "Register Contents";
  serializeJson(messageDoc, Serial);
  Serial.println();
	for(index=0; index < 18 ; index++)
	{
		cTemp = adc.regRead(index);
    messageDoc["type"] = "Info";
    messageDoc["message"] = "Register 0x%02x = 0x%02x\n", index, cTemp;
    serializeJson(messageDoc, Serial);
    Serial.println();
	}
}

char command[20];
int serial_read()
{
  unsigned int n = 0;
  memset(command, 0, sizeof(command));

  while (Serial.available() > 0)
  {
    command[n++] = Serial.read();
    //delayMicroseconds(2000);
  }
  return(n);
}

enum command
{
  _REF
};

void parse_command()
{
  char *tokens[4];
  int token0[2] = {-1, -1};
  char delim[] = " ";
  int numCommands = 0;

  if(command[0] == 0x00)
  {
     return;
  }
  
  char *ptr = strtok(command, delim);
  while(ptr != NULL)
	{
    tokens[numCommands] = ptr;
		ptr = strtok(NULL, delim);
    numCommands++;
	}

/*If/else statement that assigns 'token0' variable with the enumerated 
  command, based on the first word of the recieved command string. */
  if((!strcmp(tokens[0], "REF\n")) || (!strcmp(tokens[0], "REF")))
  {
    token0[0] = _REF;
  }

  switch(token0[0])
  {
    case _REF:
    {
      
      if(!strcmp(tokens[1], "ON"))
      {
        messageDoc["type"] = "Info";
        messageDoc["message"] = "Ref On";
        serializeJson(messageDoc, Serial);
        Serial.println();
        refOn = true;
      }
      else if(!strcmp(tokens[1], "OFF"))
      {
        messageDoc["type"] = "Info";
        messageDoc["message"] = "Ref Off";
        serializeJson(messageDoc, Serial);
        Serial.println();
        refOn = false;
      }
    }
    break;
    default:
      messageDoc["type"] = "Error";
      messageDoc["message"] = "ERROR UNKNOWN COMMAND";
      serializeJson(messageDoc, Serial);
      Serial.println();
  }

  Serial.flush();
}

#define bitRead(value, bit) (((value) >> (bit)) & 0x01)
#define bitSet(value, bit) ((value) |= (1UL << (bit)))
#define bitClear(value, bit) ((value) &= ~(1UL << (bit)))
 // #define bitWrite(value, bit, bitvalue) (bitvalue ? bitSet(value, bit) : bitClear(value, bit)) // Defined in wiring.h


// setup() runs once, when the device is first turned on.
void setup() {
  Serial.begin(9600);

  tsaDoc["data"] = "thermistors";
  JsonArray data = tsaDoc["temps"].to<JsonArray>();
  data.add(0.0);
  data.add(0.0);
  data.add(0.0);
  data.add(0.0);
  data.add(0.0);
  data.add(0.0);
  data.add(0.0);

  messageDoc["type"] = "Info";

  // ADC Init
  adc.begin();
  delay(10);
  adc.sendCommand(RESET_OPCODE_MASK);

  /* print out the chip name */
  while(adc.regRead(STATUS_ADDR_MASK) != 0x80)
  {
    messageDoc["type"] = "Error";
    messageDoc["message"] = "ADC 1 not found, retrying.";
    serializeJson(messageDoc, Serial);
    Serial.println();
    delay(500);
  }
  if( adc.regRead(ID_ADDR_MASK) == 0x00 )
  {
    messageDoc["type"] = "Info";
    messageDoc["message"] = "ADC 1 found";
    serializeJson(messageDoc, Serial);
    Serial.println();
    adc.regWrite(STATUS_ADDR_MASK, 0x00);
  }
  delay(10);

  // SET INTERRUPT HANDLER TO CATCH CONVERSION READY
  pinMode(2, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(2), adsReady_1, FALLING);

  // Start First Conversion
  configureAdc_thermistor(adc_in[channel_1].AIN_P, adc_in[channel_1].AIN_N); // Start on thermistor 1
  //delay(50);
}

unsigned int act;
// Global variable to store the timestamp of the last message
unsigned long lastMessageTime = 0;
const unsigned long messageInterval = 5000; // 5000 milliseconds = 5 seconds

void loop() {
  unsigned long currentTime = millis();

  if(RDY_1)
  {
    handleConversion();
    RDY_1 = false;
  }
  // Check if more than 'messageInterval' milliseconds have passed
  if (currentTime - lastMessageTime >= messageInterval) {
    // Send the "Alive and working" message
    messageDoc["type"] = "Info";
    messageDoc["message"] = "Alive and working.";
    serializeJson(messageDoc, Serial);
    Serial.println();

    // Update 'lastMessageTime' with the current time
    lastMessageTime = currentTime;
  }

  uint8_t status;
  uint8_t rdy    = bitRead(status, 6);
  uint8_t por    = bitRead(status, 7);

  if(statusOld != dStatus )
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
      //configureAdc_thermistor(adc_in[channel_1].AIN_P, adc_in[channel_1].AIN_N);
      // print debug info so we can see if this worked
      status = adc.regRead( STATUS_ADDR_MASK );
      Serial.print( "POR cleared? " );
      Serial.println(status,BIN);
    }
  }
}

//  catch interrupt and set flag device 1
void adsReady_1()
{
  RDY_1 = true;
  // handleConversion();
}

bool handleConversion()
{
  bool rv = false;
  if (RDY_1)
  {
    readData(adc, adc_in[channel_1].isRef);
    adc.sendCommand(STOP_OPCODE_MASK);

    channel_1++;
    if (channel_1 >= NUM_THERMISTORS) 
    {
      act = serial_read(); // Check for serial data
      if(act)
      {
        parse_command();
      }
      if(!refOn)
      {
        tsaDoc["temps"][0] = temps[0];
        tsaDoc["temps"][1] = temps[1];
        tsaDoc["temps"][2] = temps[2];
        tsaDoc["temps"][3] = temps[3];
        tsaDoc["temps"][4] = temps[4];
        tsaDoc["temps"][5] = temps[5];
        tsaDoc["temps"][6] = 0.0;
      }
      else
      {
        configureAdc_thermistor(adc_in[6].AIN_P, adc_in[6].AIN_N);
        readData(adc, adc_in[6].isRef);

        tsaDoc["temps"][0] = temps[0];
        tsaDoc["temps"][1] = temps[1];
        tsaDoc["temps"][2] = temps[2];
        tsaDoc["temps"][3] = temps[3];
        tsaDoc["temps"][4] = temps[4];
        tsaDoc["temps"][5] = temps[5];
        tsaDoc["temps"][6] = temps[6];
      }
      serializeJson(tsaDoc, Serial);
      Serial.println();
      channel_1 = 0;
    }
    delay(2);
    configureAdc_thermistor(adc_in[channel_1].AIN_P, adc_in[channel_1].AIN_N);
    rv = true;
  }
  return rv;
}