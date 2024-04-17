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

// Desired temperature range to be used with reference sensors
const int dataPoints = 111; // Total number of data points
const float temperatures[dataPoints] = {
  0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 
  10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 
  20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 
  30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 
  40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 
  50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 
  60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 
  70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 
  80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 
  90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 
  100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 
  110
};

// Look-up table for thermistor reference sensor
const float resistancesTherm[dataPoints] = {
  29490.0, 28150.0, 26890.0, 25690.0, 24550.0, 23460.0, 22430.0, 21450.0, 20520.0, 19630.0, 
  18790.0, 17980.0, 17220.0, 16490.0, 15790.0, 15130.0, 14500.0, 13900.0, 13330.0, 12790.0, 
  12260.0, 11770.0, 11290.0, 10840.0, 10410.0, 10000.0, 9605.0, 9227.0, 8867.0, 8523.0, 
  8194.0, 7880.0, 7579.0, 7291.0, 7016.0, 6752.0, 6500.0, 6258.0, 6026.0, 5805.0, 
  5592.0, 5389.0, 5193.0, 5006.0, 4827.0, 4655.0, 4489.0, 4331.0, 4179.0, 4033.0, 
  3893.0, 3758.0, 3629.0, 3504.0, 3385.0, 3270.0, 3160.0, 3054.0, 2952.0, 2854.0, 
  2760.0, 3669.0, 2582.0, 2497.0, 2417.0, 2339.0, 2264.0, 2191.0, 2122.0, 2055.0, 
  1990.0, 1928.0, 1868.0, 1810.0, 1754.0, 1700.0, 1648.0, 1598.0, 1549.0, 1503.0, 
  1458.0, 1414.0, 1372.0, 1332.0, 1293.0, 1255.0, 1218.0, 1183.0, 1149.0, 1116.0, 
  1084.0, 1053.0, 1023.0, 994.2, 966.3, 939.3, 913.2, 887.9, 863.4, 839.7, 
  816.8, 794.6, 773.1, 752.3, 732.1, 712.6, 693.6, 675.3, 657.5, 640.3, 
  623.5
};


// Look up table for RTD-100 reference sensor
const float resistancesRTD[dataPoints] = {
 100.0, 100.39, 100.78, 101.17, 101.56, 101.95, 102.34, 102.73, 103.12, 103.51, 
 103.9, 104.29 ,104.68, 105.07, 105.46, 105.85, 106.24, 106.63, 107.02, 107.4, 
 107.79, 108.18, 108.57, 108.96, 109.35, 109.73, 110.12, 110.51, 110.9, 111.28,
 111.67, 112.06, 112.45, 112.83, 113.22, 113.61, 113.99, 114.38, 114.77, 115.15,
 115.54, 115.93, 116.31, 116.7, 117.08, 117.47, 117.85, 118.24, 118.62, 119.01, 
 119.4, 119.78, 120.16, 120.55, 120.93, 121.32, 121.7, 122.09, 122.47, 122.86, 
 123.24, 123.62, 124.01, 124.39, 124.77, 125.17, 125.55, 125.93, 126.32, 126.7,
 127.08, 127.46, 127.85, 128.23, 128.61, 128.99, 129.38, 129.76, 130.14, 130.52,
 130.9, 131.28, 131.67, 132.05, 132.43, 132.81, 133.19, 133.57, 133.95, 134.33, 
 134.71, 135.09,135.47, 135.85, 136.23, 136.61, 136.99, 137.37, 137.75, 138.13, 
 138.51, 138.89, 139.27, 139.65, 140.03, 140.39, 140.77, 141.15, 141.53, 141.91,
 142.29
 };

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

// // For Reference SIA
// struct adc_inputs adc_in[] = 
// {
//   {"T1", ADS_P_AIN0, ADS_N_AIN9, true},   // thermistor1
//   {"T2", ADS_P_AIN2, ADS_N_AIN9, true},   // thermistor2
//   {"T3", ADS_P_AIN6, ADS_N_AIN9, true},   // thermistor3
//   {"T4", ADS_P_AIN4, ADS_N_AIN9, true},   // thermistor4
//   {"T5", ADS_P_AIN8, ADS_N_AIN9, false},   // thermistor5
//   {"T6", ADS_P_AIN10, ADS_N_AIN9, false},  // thermistor6
//   {"Ref", ADS_P_AIN1, ADS_N_AIN9, true}    // Ref Sensor
// };

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

  adc.regWrite( DATARATE_ADDR_MASK, ADS_CONVMODE_SS + ADS_FILTERTYPE_S3 + ADS_DR_50);

  adc.sendCommand(START_OPCODE_MASK);
  delay(50);
}

// TSA thermistor - Resistance to temperature calculation function
float getCelcius( float thermistance )
 {
    float temp_C = (1/((1/TEMPERATURENOMINAL) + BCOEFFICIENT*log(thermistance/THERMISTORNOMINAL))) - 273.15;   // Convert thermistance to temperature
    temps[channel_1] = temp_C;
    return temp_C;
 }

// Reference thermistor - Resistance to temperature look-up function
float getCelcius2(float resistance) {
    if (resistance >= resistancesTherm[0]) 
    {
        temps[channel_1] = temperatures[0];
        return temperatures[0];
    } 
    else if (resistance <= resistancesTherm[dataPoints - 1]) 
    {
        temps[channel_1] = temperatures[dataPoints - 1];
        return temperatures[dataPoints - 1];
    }
    for (int i = 0; i < dataPoints - 1; i++) {
        if (resistance >= resistancesTherm[i + 1] && resistance <= resistancesTherm[i]) {
            // Linear interpolation
            float tempDiff = temperatures[i] - temperatures[i + 1];
            float resDiff = resistancesTherm[i] - resistancesTherm[i + 1];
            float fraction = (resistance - resistancesTherm[i + 1]) / resDiff;
            float temp_C = temperatures[i + 1] + (tempDiff * fraction);
            temps[channel_1] = temp_C;
            return temp_C;
        }
    }
    // Default case, should not be reached
    return -999; // Indicates an error
}

// Reference RTD - Resistance to temperature look-up function
float getCelcius3(float resistance) {
    if (resistance <= resistancesRTD[0]) 
    {
        temps[channel_1] = temperatures[0];
        return temperatures[0];
    } 
    else if (resistance >= resistancesRTD[dataPoints - 1]) 
    {
        temps[channel_1] = temperatures[dataPoints - 1];
        return temperatures[dataPoints - 1];
    }
    for (int i = 0; i < dataPoints - 1; i++) 
    {
        if (resistance <= resistancesRTD[i + 1] && resistance >= resistancesRTD[i]) {
            // Linear interpolation
            float tempDiff = temperatures[i] - temperatures[i + 1];
            float resDiff = resistancesRTD[i] - resistancesRTD[i + 1];
            float fraction = (resistance - resistancesRTD[i + 1]) / resDiff;
            float temp_C = temperatures[i + 1] + (tempDiff * fraction);
            temps[channel_1] = temp_C;
            return temp_C;
        }
    }
    // Default case, should not be reached
    return -999; // Indicates an error
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
    getCelcius3(thermistance);
  }
  else 
  {
    getCelcius2(thermistance);
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