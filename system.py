#!/usr/bin/env python3.5
# -*- coding:utf-8 -*-
import serial
import time
import threading
import sys
import json
import smtplib
import os
import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QMessageBox, QHBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence, QFont
import RPi.GPIO as GPIO
from PIL import Image,ImageDraw,ImageFont

# Packet Identify code
Command                 = 0xAA55
Response                = 0x55AA
Command_Data            = 0xA55A
Response_Data           = 0x5AA5

# Soruce Device ID
Command_SID             = 0x00
Response_SID            = 0x01

# Destination Device ID 
Command_DID             = 0x00
Response_DID            = 0x00

# Command Code and Response Code
CMD_TEST_CONNECTION     = 0x01
CMD_FINGER_DETECT       = 0x21
CMD_GET_IMAGE           = 0x20
CMD_GENERATE            = 0x60
CMD_MERGE               = 0x61
CMD_DEL_CHAR            = 0x44
CMD_STORE_CHAR          = 0x40
CMD_SEARCH              = 0x63
CMD_VERIFY 				= 0x64
CMD_GET_EMPTY_ID 		= 0x45
CMD_GET_ENROLL_COUNT 	= 0x48
CMD_DOWN_IMAGE 			= 0x23
CMD_UP_IMAGE_CODE 		= 0x22

# Result Code  		
ERR_SUCCESS				= 0x00
ERR_FAIL				= 0x01
ERR_TIME_OUT			= 0x23
ERR_FP_NOT_DETECTED		= 0x28
ERR_FP_CANCEL			= 0x41
ERR_INVALID_BUFFER_ID	= 0x26
ERR_BAD_QUALITY			= 0x19
ERR_GEN_COUNT			= 0x25
ERR_INVALID_TMPL_NO		= 0x1D
ERR_DUPLICATION_ID		= 0x18
ERR_INVALID_PARAM		= 0x22
ERR_TMPL_EMPTY			= 0x12
ERR_VERIFY				= 0x10
ERR_IDENTIFY			= 0x11

# Length of DATA
DATA_0					= 0x0000		
DATA_1					= 0x0001		
DATA_2					= 0x0002		
DATA_3					= 0x0003		
DATA_4					= 0x0004		
DATA_5					= 0x0005		
DATA_6					= 0x0006		
DATA_38					= 0x0026		
DATA_498				= 0x01F2
DATA_390				= 0x0186

# Command structure
CMD_Len  				= 16
RPS_Len 				= 14
CMD_Packet_Len  		= 498
RPS_Packet_Len  		= 498

Finger_RST_Pin    		= 24
TRUE       				= 1
FALSE        			= 0
Tx_flag        			= 0

# Checkout Variables
emptyID = 1
savedID = 1
userID = 1

picdir = os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__))), 'pic')

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Finger_RST_Pin, GPIO.OUT) 
GPIO.setup(Finger_RST_Pin, GPIO.OUT, initial=GPIO.HIGH)

ser = serial.Serial("/dev/ttyS0", 115200)
cmd = [0x55, 0xAA ,0x00 ,0x00 ,0x01 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00 ,0x00, 0x00 ,0x01]
rps = [0x00] * 26
cmd_data = [0xff] * 508
cmd_data1 = [0xff] * 400


class Cmd_Packet:
    def __init__(self):
        self.PREFIX = 0x0000
        self.SID 	= 0x00
        self.DID 	= 0x00
        self.CMD 	= 0x00
        self.LEN 	= 0x0000
        self.DATA 	= [0x00] * 16
        self.CKS 	= 0x0000

class Rps_Packet:
    def __init__(self):
        self.PREFIX = 0x0000
        self.SID 	= 0x00
        self.DID 	= 0x00
        self.CMD 	= 0x00
        self.LEN 	= 0x0000
        self.RET 	= 0x0000
        self.DATA 	= [0x00] * 14
        self.CKS 	= 0x0000	

class Command_Packet:
    def __init__(self):
        self.PREFIX = 0x0000
        self.SID 	= 0x00
        self.DID 	= 0x00
        self.CMD 	= 0x00
        self.LEN 	= 0x0000
        self.DATA 	= [0x00] * 498
        self.CKS 	= 0x0000

class Response_Packet:
    def __init__(self):
        self.PREFIX = 0x0000
        self.SID 	= 0x00
        self.DID 	= 0x00
        self.CMD 	= 0x00
        self.RCM    = 0X0000
        self.LEN 	= 0x0000
        self.RET 	= 0x0000
        self.DATA 	= [0x00] * 498
        self.CKS 	= 0x0000	

CMD = Cmd_Packet()
RPS = Rps_Packet()
CMD_DATA = Command_Packet()
RPS_DATA = Response_Packet()

# /***************************************************************************
# * @brief      Build the command array and send it
# ****************************************************************************/
def Tx_cmd():
    CKS = 0
    cmd[0] = CMD.PREFIX & 0xff
    cmd[1] = (CMD.PREFIX & 0xff00) >> 8
    cmd[2] = CMD.SID
    cmd[3] = CMD.DID
    cmd[4] = CMD.CMD
    cmd[5] = 0x00
    cmd[6] = CMD.LEN & 0xff
    cmd[7] = (CMD.LEN & 0xff00) >> 8
    for i in range(CMD.LEN):
        cmd[8+i] = CMD.DATA[i]
    for i in range(24):
        CKS = CKS + cmd[i]
    cmd[24] = CKS & 0xff
    cmd[25] = (CKS & 0xff00) >> 8
    ser.write(cmd)   

# /***************************************************************************
# * @brief      Build the command array and send it
# ****************************************************************************/
def Tx_cmd_data(SN):
    CKS = 0
    cmd_data[0] = CMD_DATA.PREFIX & 0xff
    cmd_data[1] = (CMD_DATA.PREFIX & 0xff00) >> 8
    cmd_data[2] = CMD_DATA.SID
    cmd_data[3] = CMD_DATA.DID
    cmd_data[4] = CMD_DATA.CMD
    cmd_data[5] = 0x00
    cmd_data[6] = CMD_DATA.LEN & 0xff
    cmd_data[7] = (CMD_DATA.LEN & 0xff00) >> 8
    if SN<129:
        for i in range(CMD_DATA.LEN):
            cmd_data[8+i] = CMD_DATA.DATA[i]
        for i in range(506):
            CKS = CKS + cmd_data[i]
            cmd_data[506] = CKS & 0xff
            cmd_data[507] = (CKS & 0xff00) >> 8

        ser.write(cmd_data)
    else :
        for i in range(CMD_DATA.LEN):
            cmd_data[8+i] = CMD_DATA.DATA[i]
        for i in range(398):
            CKS = CKS + cmd_data[i]
            cmd_data[398] = CKS & 0xff
            cmd_data[399] = (CKS & 0xff00) >> 8
        ser.write(cmd)


# /***************************************************************************
# * @brief      Receive user commands and process them
# ****************************************************************************/
def Tx_Data_Process(str):
    while(1):
        if len(str) < 4:
            continue
        if((str[0] == 'C') & (str[1] == 'M') & (str[2] == 'D')):
            if str[3] == '0':
                CmdTestConnection( 0 )
            elif str[3] == '1':
                CmdFingerDetect( 0 )
            elif str[3] == '2':
                AddUser()
                break
            elif str[3] == '3':
                ClearUser( 0 )
            elif str[3] == '4':
                VerifyUser()
            elif str[3] == '5':
                ScopeVerifyUser()
                break
            elif str[3] == '6':
                CmdGetEmptyID( 0 )
            elif str[3] == '7':
                GetUserCount( 1 )
            elif str[3] == '8':
                CmdUpImageCode( 1 )
            elif str[3] == '9':
                CmdDownImage()
            else:
                time.sleep(0.01)
    return 0

# /***************************************************************************
# * @brief      Connect the test
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdTestConnection( back ):
    CMD.CMD = CMD_TEST_CONNECTION
    CMD.LEN = DATA_0
    Tx_cmd()
    return Rx_cmd(back)

# /***************************************************************************
# * @brief      To detect
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdFingerDetect( back ):
    CMD.CMD = CMD_FINGER_DETECT
    CMD.LEN = DATA_0
    Tx_cmd()
    return Rx_cmd(back)

# /***************************************************************************
# * @brief      Capture fingerprint image
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdGetImage( back ):
	CMD.CMD = CMD_GET_IMAGE
	CMD.LEN = DATA_0
	Tx_cmd()
	return Rx_cmd(back)

# /***************************************************************************
# * @brief      Generates a template from a fingerprint image that is temporarily stored in the ImageBuffer
# * @param      k			Stored in the RamBuffer 0 to 10
# 							back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdGenerate( k , back ):
	CMD.CMD = CMD_GENERATE
	CMD.LEN = DATA_2
	CMD.DATA[0] = k 
	CMD.DATA[1] = 0x00 
	Tx_cmd()
	return Rx_cmd(back)

# /***************************************************************************
# * @brief      Generates a template from a fingerprint image that is temporarily stored in the ImageBuffer
# * @param      k			The synthesized fingerprint is stored in the RamBuffer 0~10
# 							n			Synthesize several RamBuffer templates 2 or 3
# 							back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdMerge( k , n , back ):
	CMD.CMD = CMD_MERGE
	CMD.LEN = DATA_3
	CMD.DATA[0] = k 
	CMD.DATA[1] = 0x00 
	CMD.DATA[2] = n 
	Tx_cmd()
	return Rx_cmd(back)

# /***************************************************************************
# * @brief      Save the fingerprint template data to the fingerprint database of the module
# * @param      k			Save the fingerprint to storage location K	 1~3000
# 							n			Save the fingerprint template of the NTH RamBuffer
# 							back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdStoreChar( k , n , back ):
	CMD.CMD = CMD_STORE_CHAR
	CMD.LEN = DATA_4
	CMD.DATA[0] = k 
	CMD.DATA[1] = 0x00 
	CMD.DATA[2] = n 
	CMD.DATA[3] = 0x00 
	Tx_cmd()
	return Rx_cmd(back)

# /***************************************************************************
# * @brief      Register fingerprint
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def AddUser():
    CMD.CMD = CMD_GET_EMPTY_ID
    CMD.LEN = DATA_4
    CMD.DATA[0] = 0x01
    CMD.DATA[1] = 0x00
    CMD.DATA[2] = 0xB8
    CMD.DATA[3] = 0x0B
    Tx_cmd()
    Rx_cmd(1)
    data = RPS.DATA[0] + RPS.DATA[1] * 0x0100
    emptyID = data
    print("The recommended registration number is : %d"%data)
    Data = TX_DATA(1)
    k = (Data & 0xffff0000) >> 16

    for a in range(3):
        for i in range(3):
            if not CmdFingerDetect(1):
                print("Please move your finger away")
            while not CmdFingerDetect(1):
                time.sleep(0.01)
            print("Please press your finger")
            while CmdFingerDetect( 1 ):
                time.sleep(0.01)
            if not CmdFingerDetect( 1 ):
                if not CmdGetImage( 1 ):
                    if not CmdGenerate(a, 1):
                        break

    if i == 2:
        print("Fingerprint entry failure\r\n")
        return 1
    if not CmdMerge(0,3,1):
        if not CmdStoreChar(k,0,0):
            print("The fingerprint is saved successfully, and the id is : %d\r\n"%k)
            savedID = k
    else :
        print("Fingerprint entry failure\r\n")


    return 0

# /***************************************************************************
# * @brief      Clear fingerprints
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def ClearUser( back ):
    data = TX_DATA(0)
    k = (data & 0xffff0000) >> 16
    n = data & 0xffff

    CMD.CMD = CMD_DEL_CHAR
    CMD.LEN = DATA_4
    CMD.DATA[0] = k & 0xff
    CMD.DATA[1] = (k & 0xff00) >> 8
    CMD.DATA[2] = n & 0xff
    CMD.DATA[3] = (n & 0xff00) >> 8
    Tx_cmd()
    return Rx_cmd(back)

# /***************************************************************************
# * @brief      Fingerprint matching
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def VerifyUser():
    data = TX_DATA(1)
    Data = (data & 0xffff0000) >> 16

    for i in range(3):
        if not CmdFingerDetect(1):
            print("Please move your finger away")
        while not CmdFingerDetect(1):
            time.sleep(0.01)
        print("Please press your finger")
        while CmdFingerDetect( 1 ):
            time.sleep(0.01)
        if not CmdFingerDetect( 1 ):
            if not CmdGetImage( 1 ):
                if not CmdGenerate(0, 1):
                    break
    if i == 2:
        print("Fingerprint entry failure\r\n")
        return 1

    CMD.CMD = CMD_VERIFY
    CMD.LEN = DATA_4
    CMD.DATA[0] = Data & 0xff
    CMD.DATA[1] = (Data & 0xff00) >> 8
    CMD.DATA[2] = 0x00
    CMD.DATA[3] = 0x00
    Tx_cmd()
    return Rx_cmd(0)

# /***************************************************************************
# * @brief      Range fingerprint matching
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def ScopeVerifyUser():
    data = TX_DATA(0)
    k = (data & 0xffff0000) >> 16
    n = data & 0xffff

    for i in range(3):
        if not CmdFingerDetect(1):
            print("Please move your finger away")
        while not CmdFingerDetect(1):
            time.sleep(0.01)
        print("Please press your finger")
        while CmdFingerDetect( 1 ):
            time.sleep(0.01)
        if not CmdFingerDetect( 1 ):
            if not CmdGetImage( 1 ):
                if not CmdGenerate(0, 1):
                    break

    if i==2:
        print("Fingerprint entry failure\r\n")
        return 1

    CMD.CMD = CMD_SEARCH
    CMD.LEN = DATA_6
    CMD.DATA[0] = 0x00
    CMD.DATA[1] = 0x00
    CMD.DATA[2] = k & 0xff 
    CMD.DATA[3] = (k & 0xff00) >> 8
    CMD.DATA[4] = n & 0xff
    CMD.DATA[5] = (n & 0xff00) >> 8
    Tx_cmd()
    return Rx_cmd(0)

# /***************************************************************************
# * @brief      Gets the first number in a range of numbers that can be registered
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdGetEmptyID(back):
	data = TX_DATA(0)
	k = (data & 0xffff0000) >> 16
	n = data & 0xffff
	
	CMD.CMD = CMD_GET_EMPTY_ID
	CMD.LEN = DATA_4
	CMD.DATA[0] = k & 0xff
	CMD.DATA[1] = (k & 0xff00) >> 8
	CMD.DATA[2] = n & 0xff
	CMD.DATA[3] = (n & 0xff00) >> 8 
	Tx_cmd()
	return Rx_cmd(back)

# /***************************************************************************
# * @brief      Query the number of existing fingerprints
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def GetUserCount(back):
	data = TX_DATA(0)
	k = (data & 0xffff0000) >> 16
	n = data & 0xffff
	
	CMD.CMD = CMD_GET_ENROLL_COUNT
	CMD.LEN = DATA_4
	CMD.DATA[0] = k & 0xff
	CMD.DATA[1] = (k & 0xff00) >> 8
	CMD.DATA[2] = n & 0xff
	CMD.DATA[3] = (n & 0xff00) >> 8 
	Tx_cmd()
	return Rx_cmd(not back)


# /***************************************************************************
# * @brief      Upload fingerprint image to host
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdUpImageCode(back):
    Rx_data = []
    if not CmdFingerDetect(back):
        print("Please move your finger away")
    while not CmdFingerDetect(back):
        time.sleep(0.01)
    print("Please press your finger")
    while CmdFingerDetect( back ):
        time.sleep(0.01)
    if not CmdFingerDetect( back ):
        if not CmdGetImage( back ):
            print("Please wait while data is being received")
            CMD.CMD = CMD_UP_IMAGE_CODE
            CMD.LEN = DATA_1
            CMD.DATA[0] = 0x00 
            Tx_cmd()
            time.sleep(0.1)
            while ser.inWaiting()>0:
                for i in range(66218):
                    Rx_data.append(ord(ser.read()))
            Data_Txt(Rx_data)
    return 0

# /***************************************************************************
# * @brief      The received fingerprint template data is written to the TXT document
# * @param      Rx_data 	Fingerprint Template Data
# ****************************************************************************/
def Data_Txt(Rx_data):
    output = open('data.txt','w',encoding='gbk')
    i = 38
    for j in range(129):
        for o in range(8):
            for p in range(62):
                output.write("0x%x,"%Rx_data[i])
                i = i + 1
            output.write('\n')
        i = i + 14
    for j in range(6):
        for p in range(62):
            output.write("0x%x,"%Rx_data[i])
            i = i + 1
        output.write('\n')
    for p in range(8):
        output.write("0x%x,"%Rx_data[i])
        i = i + 1
    print("To write to the data.txt document")



# /***************************************************************************
# * @brief      Download the fingerprint image to the module
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def CmdDownImage():
    print("Please wait while writing fingerprint image")
    CMD.CMD = CMD_DOWN_IMAGE
    CMD.LEN = DATA_4
    CMD.DATA[0] = 242 & 0xff
    CMD.DATA[1] = (242 & 0xff00) >> 8
    CMD.DATA[2] = 266 & 0xff
    CMD.DATA[3] = (266 & 0xff00) >> 8
    Tx_cmd()
    Rx_cmd(0)

    Himage = Image.open(os.path.join(picdir, '2.bmp'))
    image_monocolor = Himage.convert('L')
    imwidth, imheight = image_monocolor.size
    pixels = image_monocolor.load()

    CMD_DATA.PREFIX = Command_Data
    CMD_DATA.SID = Command_SID
    CMD_DATA.DID = Command_DID
    CMD_DATA.CMD = CMD_DOWN_IMAGE
    CMD_DATA.LEN = DATA_498
    length = 0
    width = 0
    for SN in range(129):
        CMD_DATA.DATA[0] = SN & 0xff 
        CMD_DATA.DATA[1] = (SN & 0xff00) >> 8
        for i in range(496):
            CMD_DATA.DATA[i+2] = pixels[width,length]
            width = width + 1
            if width > 241 :
                width = 0
                length = length + 1
        Tx_cmd_data(SN)
        fun = Rx_cmd_ten(0)
        if fun:
            print("Write Error")
            return 1
    CMD_DATA.LEN = DATA_390
    CMD_DATA.DATA[0] = SN & 0xff 
    CMD_DATA.DATA[1] = (SN & 0xff00) >> 8
    for i in range(388):
        CMD_DATA.DATA[i+2] = pixels[width,length]
        width = width + 1
        if width > 241 :
            width = 0
            length = length + 1
    Tx_cmd_data( SN+1 )
    fun = Rx_cmd(0)
    if fun:
        print("Write Error")
        return 1

    CmdGenerate(0, 1) 
    CMD.CMD = CMD_GET_EMPTY_ID
    CMD.LEN = DATA_4
    CMD.DATA[0] = 0x01
    CMD.DATA[1] = 0x00
    CMD.DATA[2] = 0xB8 
    CMD.DATA[3] = 0x0B 
    Tx_cmd()
    Rx_cmd(1)
    data = RPS.DATA[0] + RPS.DATA[1] * 0x0100
    if( not CmdStoreChar(data,0,0) ):
        print("The fingerprint is saved successfully, and the id is : %d\r\n"%data)
    return 0

# /***************************************************************************
# * @brief      Range set receive
# * @return     Range
# ****************************************************************************/
def TX_DATA(Tx_flag):
    a = 0
    while(1):
        data_start = 0
        data_end = 0
        if(Tx_flag):
            str = f"{emptyID}"
            a = len(str)
            if(a > 4):
                print(f"please input again")
                continue
            else:
                for i in range(a):
                    data_start = data_start * 10 + ord(str[i]) - 0x30
                if((data_start > 3000) | (data_start < 1)):
                    print("please input again")
                    continue
                break
        else:
            str = "1,3000"
            a = len(str)
            if ((a > 9) | (a<3)):
                print("please input again")
                continue
            else:
                i = 0
                while str[i] != ',':
                    data_start = data_start * 10 + ord(str[i]) - 0x30
                    i = i+1
                    if((i>3) | (i==a)):
                        break
                if((data_start > 3000) | (data_start < 1) | (i>3)):
                    print("please input again")
                    continue
                i = i + 1
                while i<a:
                    data_end = data_end * 10 + ord(str[i]) - 0x30
                    i = i+1
                if((data_end > 3000) | (data_end < 1)):
                    print("please input again")
                    continue
                break
    Data = data_start * 0x10000 + data_end
    return Data

# /***************************************************************************
# * @brief      Receive response array
# * @param      back	0 Print return status
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def Rx_cmd(back):
    a=1
    CKS = 0
    while a:
        while ser.inWaiting()>0:
            for i in range(26):
                rps[i] =ord(ser.read())
            a = 0
            if rps[4] == 0xff:
                return 1
            Rx_CMD_Process(1)
            for i in range(24):
                CKS = (CKS + rps[i])&0xffff
            if CKS == RPS.CKS:
                return Rx_Data_Process(back)
    return 1

# /***************************************************************************
# * @brief      Receive response array
# * @param      back	0 Print return status
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def Rx_cmd_ten(back):
    a=1
    CKS = 0
    while a:
        while ser.inWaiting()>0:
            for i in range(12):
                rps[i] =ord(ser.read())
            a = 0
            if rps[4] == 0xff:
                return 1
            Rx_CMD_Process(0)
            for i in range(10):
                CKS = (CKS + rps[i])&0xffff
            if CKS == RPS.CKS:
                return Rx_Data_Process(back)
    return 1

def Rx_cmd_data(back):
     while a:
        while ser.inWaiting()>0:
            print(hex(ord(ser.read())))


# /***************************************************************************
# * @brief      Place the response data in the structure
# ****************************************************************************/
def Rx_CMD_Process(flag):
    RPS.PREFIX = rps[0] + rps[1] * 0x100
    RPS.SID = rps[2]
    RPS.DID = rps[3]
    RPS.CMD = rps[4] + rps[5] * 0x100
    RPS.LEN = rps[6] + rps[7] * 0x100
    RPS.RET = rps[8] + rps[9] * 0x100
    if flag:
        for i in range(RPS_Len):
            RPS.DATA[i] = rps[10 +i]
        RPS.CKS = rps[24] + rps[25] * 0x100
    else:
        RPS.CKS = rps[10] + rps[11] * 0x100

# /***************************************************************************
# * @brief      Process the response data
# * @param      back	0 Print return status   
# 										1 Do not print return status

# * @return     0			Instruction processing succeeded
# 						rests		Instruction processing failure	
# ****************************************************************************/
def Rx_Data_Process( back ):
    a = 1
    if RPS.CMD==CMD_TEST_CONNECTION:
        a = RpsTestConnection(back)
    elif RPS.CMD==CMD_FINGER_DETECT:
        a = RpsFingerDetect(back)
    elif RPS.CMD==CMD_GET_IMAGE:
        a = RpsGetImage(back)
    elif RPS.CMD==CMD_GENERATE:
        a = RpsGenerate(back)
    elif RPS.CMD==CMD_MERGE:
        a = RpsMerge(back)
    elif RPS.CMD==CMD_DEL_CHAR:
        a = RpsDelChar(back)
    elif RPS.CMD==CMD_STORE_CHAR:
        a = RpsStoreCher(back)
    elif RPS.CMD==CMD_SEARCH:
        a = RpsSearch(back)
    elif RPS.CMD==CMD_VERIFY:
        a = RpsVerify(back)
    elif RPS.CMD==CMD_GET_EMPTY_ID:
        a = RpsGetEmptyID(back)
    elif RPS.CMD==CMD_GET_ENROLL_COUNT:
        a = RpsGetEnrollCount(back)
    elif RPS.CMD==CMD_DOWN_IMAGE:
        a = RpsDownImage(back)
    else :
        time.sleep(0.01)
    return a

# /***************************************************************************
# * @brief      Response and error code list
# ****************************************************************************/
def RPS_RET():
    if RPS.RET == ERR_SUCCESS:
        print("Instruction processing succeeded\r\n")
    elif RPS.RET == ERR_FAIL:
        print("Instruction processing failure\r\n")
    elif RPS.RET == ERR_TIME_OUT:
        print("No prints were entered within the time limit\r\n")
    elif RPS.RET == ERR_FP_NOT_DETECTED:
        print("There is no fingerprint input on the collector\r\n")
    elif RPS.RET == ERR_FP_CANCEL:
        print("Instruction cancelled\r\n")
    elif RPS.RET == ERR_INVALID_BUFFER_ID:
        print("The Ram Buffer number is invalid\r\n")
    elif RPS.RET == ERR_BAD_QUALITY:
        print("Poor fingerprint image quality\r\n")
    elif RPS.RET == ERR_GEN_COUNT:
        print("Invalid number of combinations\r\n")
    elif RPS.RET == ERR_INVALID_TMPL_NO:
        print("The specified Template number is invalid\r\n")
    elif RPS.RET == ERR_DUPLICATION_ID:
        a = RPS.DATA[0]+RPS.DATA[1]*0x100
        print("The fingerprint has been registered, and the id is : %d\r\n"%a )
    elif RPS.RET == ERR_INVALID_PARAM:
        print("Specified range invalid\r\n")
    elif RPS.RET == ERR_TMPL_EMPTY:
        print("Template is not registered in the specified range\r\n")
    elif RPS.RET == ERR_VERIFY:
        print("Description Failed to specify fingerprint comparison\r\n")
    elif RPS.RET == ERR_IDENTIFY:
        print("Fingerprint comparison failed for the specified range\r\n")
    else :
        time.sleep(0.01)
    return RPS.RET

# /***************************************************************************
# * @brief      Connection Test
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsTestConnection( back ):
    if back :
        return RPS.RET
    else :
        if RPS.RET :
            return RPS_RET()
        else :
            print("Connection successful\r\n")

            return RPS.RET

# /***************************************************************************
# * @brief      To detect
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsFingerDetect( back ):
    if back:
        if not RPS.RET :
            return not RPS.DATA[0]
    else :
        if RPS.RET :
            return RPS_RET()
        else :
            if RPS.DATA[0]:
                print("We got a print on it\r\n")
            else :
                print("No prints were detected\r\n")
            return not RPS.DATA[0]
    return 2

# /***************************************************************************
# * @brief      Capture fingerprint image
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsGetImage( back ):
	if back:
		return RPS.RET
	else :
		return RPS_RET()

# /***************************************************************************
# * @brief      Generates a template from a fingerprint image that is temporarily stored in the ImageBuffer
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsGenerate( back ):
	if back:
		return RPS.RET
	else :
		return RPS_RET()

# /***************************************************************************
# * @brief      Synthetic fingerprint template data is used for storing
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsMerge( back ):
	if back:
		return RPS.RET
	else :
		return RPS_RET()

# /***************************************************************************
# * @brief      Save the fingerprint template data to the fingerprint database of the module
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsStoreCher( back ):
	if back:
		return RPS.RET
	else :
		if RPS.RET:
			return RPS_RET()
		else :
			return RPS.RET

# /***************************************************************************
# * @brief      Erase fingerprints
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsDelChar( back ):
	if back:
		return RPS.RET
	else :
		return RPS_RET()

# /***************************************************************************
# * @brief      Compare the specified fingerprint
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsVerify( back ):
	if back:
		return RPS.RET
	else :
		if RPS.RET :
			return RPS_RET()
		else :
			print("Successful fingerprint comparison\r\n")
			return RPS.RET

# /***************************************************************************
# * @brief      Check the prints in the range
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsSearch( back ):

	if back:

		return RPS.RET

	else:

		if RPS.RET:

			return RPS_RET()
		else:
			data = RPS.DATA[0] + RPS.DATA[1] * 0x0100
			userID = data
			print("Successful fingerprint comparison")
			print("The number of the first successful match is : %d \r\n"%data)
			return RPS.RET

# /***************************************************************************
# * @brief      Gets the first number in a range of numbers that can be registered
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsGetEmptyID( back ):
	if back:
		return RPS.RET
	else :
		if RPS.RET:
			return RPS_RET()
		else :
			data = RPS.DATA[0] + RPS.DATA[1] * 0x0100
			print("The first number that can be registered within the specified range is : %d \r\n"%data)
			return RPS.RET

# /***************************************************************************
# * @brief      Gets the total number of registered fingerprints in the number range
# * @param      back: 0 Print return status   
# 										1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsGetEnrollCount(back):
	if back:
		return RPS.RET
	else :
		if RPS.RET:
			return RPS_RET()
		else :
			data = RPS.DATA[0] + RPS.DATA[1] * 0x0100;
			print("The total number of registered fingerprints in the specified range is : %d \r\n"%data);
			return RPS.RET


# /***************************************************************************
# * @brief      The fingerprint module responds to the packet
# * @param      back:   0 Print return status   
# 					    1 Do not print return status
# * @return     RPS.RET  Response and error code
# ****************************************************************************/
def RpsDownImage(back):
	return RPS.RET
	
# /***************************************************************************
# * @brief      Initialize the command structure
# ****************************************************************************/
def Cmd_Packet_Init():
    CMD.PREFIX = Command
    CMD.SID = Command_SID
    CMD.DID = Command_DID
    CMD.CMD = CMD_TEST_CONNECTION
    CMD.LEN = DATA_0
    for i in range(CMD_Len):
        CMD.DATA[i] = 0x00

# /***************************************************************************
# * @brief      main
# * @param      Boot_Mode:      0 RST pins are not used 
# 					            1 Use the RST pin
# ****************************************************************************/
def main(Boot_Mode):
    if Boot_Mode:
        GPIO.output(Finger_RST_Pin, GPIO.LOW)
        time.sleep(0.25) 
        GPIO.output(Finger_RST_Pin, GPIO.HIGH)
        time.sleep(0.25) 
        if ord(ser.read()) != 0x55 :
            print("Communication failed")
            while 1:
                time.sleep(1000)
    else :
        time.sleep(0.5)

    Cmd_Packet_Init()

    i = 0
    while 1:
        Tx_cmd()
        if Rx_cmd(1):
            print("Connection closed by server")
            i = i+1
            if(i > 3):
                print("Check the connection and reboot the device")
            while 1:
                time.sleep(1000)
        else :
            break
        time.sleep(1)

class CheckoutApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Self-Checkout System")
        self.setGeometry(0, 0, 800, 480)  # Adjust size to 7" touchscreen resolution
        self.showFullScreen()
        
        self.scanned_items = []
        self.users = []
        self.items = []
        self.barcode_buffer = ""
        
        self.load_items()
        self.load_users()

        self.item_page_open = False
        self.user_page_open = False
        self.payment_page_open = False
        
        self.main_layout = QVBoxLayout()
        
        self.scan_label = QLabel("Scanned Items:\n")
        self.scan_label.setAlignment(Qt.AlignTop)
        font = QFont()
        font.setPointSize(16)
        self.scan_label.setFont(font)
        self.main_layout.addWidget(self.scan_label)
        
        self.payment_button = QPushButton("Payment")
        self.payment_button.clicked.connect(self.open_payment_page)
        self.main_layout.addWidget(self.payment_button)
        
        self.setLayout(self.main_layout)
        
        self.item_page_shortcut = QKeySequence(Qt.CTRL + Qt.Key_I)
        self.user_page_shortcut = QKeySequence(Qt.CTRL + Qt.Key_U)
        self.esc_shortcut = QKeySequence(Qt.Key_Escape)

    # Handle barcode & command input
    def keyPressEvent(self, event):
        if event.key() in range(Qt.Key_0, Qt.Key_9 + 1):
            self.barcode_buffer += chr(event.key())
            return

        # Barcode
        if event.key() == Qt.Key_Return:
            if self.barcode_buffer:
                self.add_item_by_barcode(self.barcode_buffer)
                self.barcode_buffer = ""
            return

        # Ctrl + I (Items page)
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_I:
            self.open_item_page()
            return

        # Ctrl + U (Users page)
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_U:
            self.open_user_page()
            return

        # Escape (Exit)
        if event.key() == Qt.Key_Escape:
            self.confirm_exit()

    def add_item_by_barcode(self, barcode):
        for item in self.items:
            if item['barcode'] == barcode:
                self.scanned_items.append(item)
                self.update_scanned_items_display()
                break

    def update_scanned_items_display(self):
        display_text = "Scanned Items:\n"
        total = 0
        for item in self.scanned_items:
            display_text += f"{item['name']} - {item['price']}WON\n"
            total += item['price']
        display_text += f"Total: {total}WON"
        self.scan_label.setText(display_text)

    def open_item_page(self):
        if not self.item_page_open and not self.user_page_open:
            self.item_page = ItemPage(self)
            self.item_page.showFullScreen()
            self.item_page_open = True  # Set flag to indicate the page is open

    def open_user_page(self):
        if not self.user_page_open and not self.item_page_open:
            self.user_page = UserPage(self)
            self.user_page.showFullScreen()
            self.user_page_open = True  # Set flag to indicate the page is open

    def open_payment_page(self):
        if not self.payment_page_open and not self.user_page_open and not self.payment_page_open:
            self.payment_page = PaymentPage(self)
            self.payment_page.showFullScreen()
            self.payment_page_open = True  # Set flag to indicate the page is open

    def confirm_exit(self):
        confirm_dialog = QMessageBox()
        confirm_dialog.setText("Are you sure you want to exit?")
        confirm_dialog.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        confirm_dialog.buttonClicked.connect(self.exit_app)
        confirm_dialog.exec_()

    def exit_app(self, button):
        if button.text() == "&Yes":
            self.save_items()
            self.save_users()
            self.close()

    def load_items(self):
        try:
            with open('items.json', 'r') as file:
                self.items = json.load(file)
        except FileNotFoundError:
            self.items = []

    def save_items(self):
        with open('items.json', 'w') as file:
            json.dump(self.items, file)

    def load_users(self):
        try:
            with open('users.json', 'r') as file:
                self.users = json.load(file)
        except FileNotFoundError:
            self.users = []

    def save_users(self):
        with open('users.json', 'w') as file:
            json.dump(self.users, file)

class ItemPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Items")
        self.setGeometry(0, 0, 800, 480)
        self.showFullScreen()
        layout = QVBoxLayout()

        self.item_table = QTableWidget()
        self.item_table.setColumnCount(3)
        self.item_table.setHorizontalHeaderLabels(['Name', 'Barcode', 'Price'])
        layout.addWidget(self.item_table)

        form_layout = QHBoxLayout()
        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("Item Name")
        form_layout.addWidget(self.name_input)
        
        self.barcode_input = QLineEdit(self)
        self.barcode_input.setPlaceholderText("Barcode")
        form_layout.addWidget(self.barcode_input)
        
        self.price_input = QLineEdit(self)
        self.price_input.setPlaceholderText("Price")
        form_layout.addWidget(self.price_input)

        add_item_button = QPushButton("Add Item")
        add_item_button.clicked.connect(self.add_item)
        form_layout.addWidget(add_item_button)

        layout.addLayout(form_layout)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.close_item_page)
        layout.addWidget(back_button)

        self.setLayout(layout)
        self.update_item_table()

    def add_item(self):
        name = self.name_input.text()
        barcode = self.barcode_input.text()
        price = float(self.price_input.text())

        self.parent().items.append({'name': name, 'barcode': barcode, 'price': price})
        self.update_item_table()
        self.parent().save_items()

    def update_item_table(self):
        self.item_table.setRowCount(0)
        for i, item in enumerate(self.parent().items):
            self.item_table.insertRow(i)
            self.item_table.setItem(i, 0, QTableWidgetItem(item['name']))
            self.item_table.setItem(i, 1, QTableWidgetItem(item['barcode']))
            self.item_table.setItem(i, 2, QTableWidgetItem(f"{item['price']}WON"))

    def close_item_page(self):
        self.parent().item_page_open = False
        self.close()

class UserPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Users")
        self.setGeometry(0, 0, 800, 480)
        self.showFullScreen()
        layout = QVBoxLayout()

        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(['ID', 'Name', 'Email', 'Balance'])
        layout.addWidget(self.user_table)

        form_layout = QHBoxLayout()

        # User ID is handled automatically by getting the first available ID from the fingerprint sensor
        """self.id_input = QLineEdit(self)
        self.id_input.setPlaceholderText("User ID")
        form_layout.addWidget(self.id_input)"""

        self.name_input = QLineEdit(self)
        self.name_input.setPlaceholderText("User Name")
        form_layout.addWidget(self.name_input)

        self.email_input = QLineEdit(self)
        self.email_input.setPlaceholderText("Email")
        form_layout.addWidget(self.email_input)

        self.balance_input = QLineEdit(self)
        self.balance_input.setPlaceholderText("Balance")
        form_layout.addWidget(self.balance_input)

        add_user_button = QPushButton("Add User")
        add_user_button.clicked.connect(self.add_user)
        form_layout.addWidget(add_user_button)

        add_clear_user_button = QPushButton("Delete User")
        add_clear_user_button.clicked.connect(self.clear_user)
        form_layout.addWidget(add_clear_user_button)

        layout.addLayout(form_layout)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.close_user_page)
        layout.addWidget(back_button)

        self.setLayout(layout)
        self.update_user_table()

    def add_user(self):
        Tx_Data_Process("CMD2")
        
        user_id = savedID
        name = self.name_input.text()
        email = self.email_input.text()
        balance = float(self.balance_input.text())

        self.parent().users.append({'id': user_id, 'name': name, 'email': email, 'balance': balance})
        self.update_user_table()
        self.parent().save_users()

    def clear_user(self):
        user_id = input("User ID to delete: ")
        Tx_Data_Process("clearUser", user_id)

        for user in self.parent().users:
            if user['id'] == user_id:
                self.parent().users.remove(user)
                break

        self.parent().users.pop
        self.update_user_table()

    def update_user_table(self):
        self.user_table.setRowCount(0)
        for i, user in enumerate(self.parent().users):
            self.user_table.insertRow(i)
            self.user_table.setItem(i, 0, QTableWidgetItem(user['id']))
            self.user_table.setItem(i, 1, QTableWidgetItem(user['name']))
            self.user_table.setItem(i, 2, QTableWidgetItem(user['email']))
            self.user_table.setItem(i, 3, QTableWidgetItem(f"{user['balance']}WON"))

    def close_user_page(self):
        self.parent().user_page_open = False
        self.close()

class PaymentPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Payment")
        self.setGeometry(0, 0, 800, 480)
        self.showFullScreen()
        layout = QVBoxLayout()

        self.total_label = QLabel(f"Total Amount: {self.calculate_total()}WON")
        layout.addWidget(self.total_label)

        self.payment_info_label = QLabel("Scan Fingerprint for Payment")
        layout.addWidget(self.payment_info_label)

        confirm_button = QPushButton("Confirm Payment")
        confirm_button.clicked.connect(self.confirm_payment)
        layout.addWidget(confirm_button)

        back_button = QPushButton("Back")
        back_button.clicked.connect(self.close_payment_page)
        layout.addWidget(back_button)

        self.setLayout(layout)

    def calculate_total(self):
        total = 0
        for item in self.parent().scanned_items:
            total += item['price']
        return total

    def confirm_payment(self):
        Tx_Data_Process("CMD5")
        for user in self.parent().users:
            print(f"user['id'] = {user['id']}")
            print(f"{userID}")
            if user['id'] == userID:
                    print("HELLO")
                    user['balance'] -= self.calculate_total()
                    self.parent().save_users
                    QMessageBox.information(self, "Payment", f"{self.calculate_total()} deducted from {user['name']}!")

                    system_email = "examplesystem@gmail.com"
                    user_email = user['email']
                    subject = f"Indybucks Payment Reciept for {user['name']}"
                    item_list = ""
                    for item in self.parent().scanned_items:
                        item_list += f"   {item['name']}                            {item['price']}WON"
                    time = datetime.datetime.now()
                    date = f"{time.year}-{time.month}-{time.day} {time.hour}:{time.minute}:{time.second}"

                    message = f"""Your Reciept for Indybucks Self-Checkout
----------------------------------------
              Payment Receipt            
----------------------------------------

Date/Time: {date}

Items Purchased:
----------------------------------------
{item_list}
----------------------------------------

Total: {self.calculate_total()}WON
Your Balance: {user['balance']}WON
----------------------------------------


Thank you for your purchase!
Please contact us for any questions.
Support: examplesupport@gmail.com

Indybucks Self-Checkout System"""
                    print("MARKER")

                    text = f"Subject: {subject}\n\n{message}"

                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(system_email, "REDACTED")
                    server.sendmail(system_email, user_email, text)

                    print("Receipt send to " + user['name'])
                    QMessageBox.information(self, "Payment", f"User {user['name']} Confirmed!")
                    break
        
        self.parent().scanned_items = []  # Clear scanned items
        self.parent().update_scanned_items_display()
        self.close_payment_page()

    def close_payment_page(self):
        self.parent().payment_page_open = False  # Reset the flag
        self.close()

if __name__ == "__main__":
    main(0)
    app = QApplication(sys.argv)
    window = CheckoutApp()
    window.show()
    sys.exit(app.exec_())
