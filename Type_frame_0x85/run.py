import serial
import serial.tools.list_ports
import time
import csv
import  os
import requests
import main_0x87_sleeppad as F87

# In EXTEND BOARD USE uart4-m0
# init serial
# Check port uart4-m0 


# list all serial is activing in orangepi

class class_Collect_Data_Sleeppad():
    def __init__(self, port_uart):
        self.port_uart = str(port_uart)
        self.state_init_uart = False # Don't init
        self.data_status_define = ['Get out of bed', 'Move in bed', 'Sit up in bed',
                                   'Sleep in bed', 'Wake up in bed', 'Heavy object in bed',
                                   'Snore', 'Weak breathing']
        #         self.data_status_define = ['Ra khỏi giường', 'Di chuyển trên giường', 'Ngồi dậy trên giường',
        # 'Ngủ trên giường', 'Thức dậy trên giường', 'Vật nặng trên giường',
        # 'Ngáy', 'Thở yếu'] translate to VietNamese
        self.data_mode_define_0x87 = ['Stands for standby mode', 'Stands for server monitoring mode', 'Stands for data debugging mode',
               'Stands for BLE debugging mode', 'Waiting for firmware update']
        self.data_error_define_0x87 = ['No error', 'The device is faulty and must to be returned to the factory']
        
        self.file_save_0x85 = 'data_0x85.csv'
        self.file_save_0x87 = 'data_0x87.csv'
        
        self.HA_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiI4NDliYzAxMzE1ZjQ0NzZlYTZiOGNhZTFhMGU0NGVmMiIsImlhdCI6MTczMzk3NjEzOCwiZXhwIjoyMDQ5MzM2MTM4fQ.3ac6ZhEvdXbG2PblTW_MdVnHfOSXRdL2w3lQzGvKREw"
        self.ip_local = "192.168.1.25"
        
        # Length data recv to filter
        self.max_length_85 = 54
        self.max_length_87 = 42
    
    def check_port_uart(self):
   
        have_uart4m0 = False

        if self.port_uart == '/dev/ttyS4': # /dev/ttyS4
            have_uart4m0 = True

        return have_uart4m0
    
        
    def collect_data_sleeppad(self):
        while True:
            try:
                if self.check_port_uart():
                    print("UART4-M0 ready!!")
                    
                    if self.state_init_uart == False:
                        self.uart4m0 = serial.Serial(self.port_uart, 115200, timeout=1)
                    
                        self.state_init_uart = True
                    else:
                        
                        print("Collect")
                        if self.uart4m0.in_waiting > 0:
                            print("Collect2")
                            data = self.uart4m0.read(self.uart4m0.in_waiting)
                            self.allDatahex_Recv = data.hex()
                            print(self.allDatahex_Recv)
                                
                            if (self.allDatahex_Recv[2:4] == '85'):
                                #Mode 85
                                if self.check_invalid_sequence(self.allDatahex_Recv, self.max_length_85):
                                    self.result_data_struct = self.analyze_all_data(self.allDatahex_Recv)
                                    print("Data Hex Receive 0x85: ", self.allDatahex_Recv)
                                    print("Dict all data Hex 0x85: ", self.result_data_struct)
                                    # Analyz_Conet_0x85
                                    self.dict_data_hex_content, self.dict_data_decimal_content = self.analyze_content_0x85(self.result_data_struct['Content/Response'])
                                    
                                    # When Sleeppad in type frame 0x85 we push No Error, Activing
                                    F87.push_data_0x87_HA("Mode", "Active", self.ip_local, self.HA_TOKEN)
                                    F87.push_data_0x87_HA("Error", self.data_error_define_0x87[0], self.ip_local, self.HA_TOKEN)
                                    
                                    
                            elif (self.allDatahex_Recv[2:4] == '87'):
                                print(f"Type frame: {self.allDatahex_Recv[2:4]}")
                                if self.check_invalid_sequence(self.allDatahex_Recv, self.max_length_87):
                                    self.result_data_struct = self.analyze_all_data(self.allDatahex_Recv)
                                    print("Data Hex Receive 0x87: ", self.allDatahex_Recv)
                                    print("Dict all data Hex 0x87: ", self.result_data_struct)
                                    self.dict_data_Real_0x87 = F87.analyze_content_0x87(self.result_data_struct['Content/Response'])
                                    print("Data Real 0x87: ", self.dict_data_Real_0x87)
                                    
                                    ######################### PUSH DATA 0x87 TO HA #########################
                                    ########## PUSH Mode
                                    F87.push_data_0x87_HA("Mode", self.dict_data_Real_0x87['Mode'], self.ip_local, self.HA_TOKEN)
                                    ########## PUSH "Error"
                                    F87.push_data_0x87_HA("Error", self.dict_data_Real_0x87['Error'], self.ip_local, self.HA_TOKEN)
                                    
                                    ########### When Sleeppad in type frame 0x87 We push all data = null of type frame 0x85
                                    
                                    dict_data_null_0x85 = {'Status': "None", # get real status
                                      'Heart_rate': None, 
                                      'Respiraton_rate': None,
                                      'SDATA':None,
                                      'PDATA': None}
                                    self.push_all_data_0x85_HA(dict_data_null_0x85)
                                    
                                    
                        # Analyze all data hex from Sleeppad at mode 0x85:
                else:
                    print("UART4-M0 failed")
                    
                    self.state_init_uart = False
                time.sleep(1)
            except Exception as e:
                print(e)
                F87.push_data_0x87_HA("Mode", "You must connect Sleeppad", self.ip_local, self.HA_TOKEN)
                F87.push_data_0x87_HA("Error", "You must connect Sleeppad", self.ip_local, self.HA_TOKEN)
                
                self.state_init_uart = False
                pass
    
    def check_invalid_sequence(self, data, max_length):
        # Tìm vị trí xuất hiện của "0d7d"
        pos = data.find("0d7d")
        
        # Kiểm tra điều kiện
        if pos != -1 and pos > max_length:
            return False  # Chuỗi không hợp lệ và trả về vị trí
        return True  # Chuỗi hợp lệ
    
    def analyze_all_data(self, all_data_recv_hex):
        '''
        Overall data structure (): 
        [frame header 0x7D is 1byte]+[frame type symbol 1byte]+[frame length 2byte]+[ID total 10byte ASCII code]+[content: data/response]+[end 0x0D] 
        
        *) content/response don't limit bytes but content only 12 bytes first. 
        7D 85 1B 00 55 4E 43 4F 4E 46 49 47 45 44 39 82 52 39 63 01 00 00 03 00 2C 01 0D 
        '''
        self.header = all_data_recv_hex[0:2]
        self.type_frame = all_data_recv_hex[2:4]
        self.frame_length = self.revert_bit_low_high(all_data_recv_hex[4:8])
        self.id_total = self.convert_hex_decimal_apair(self.revert_bit_low_high(all_data_recv_hex[8:28]))
        self.end = all_data_recv_hex[-2: ]
        self.content = all_data_recv_hex[28:-2]
        
        # dict data struct
        self.dict_data_struct = {'header':self.header, 'type_frame':self.type_frame, 'frame_length':self.frame_length, 
                                 'ID_total_Decimal':self.id_total, 'Content/Response':self.content, 'end':self.end}
        
            
        return self.dict_data_struct
    
    ################################### Type frame 0x85 #####################################
    def analyze_content_0x85(self, data_cnt):
        
        '''The content is 
        [serial number 1byte]+[time 4byte] +[status 1byte]+[heart rate 1byte]+[respiration rate 1byte]+[SDATA 2byte]+[PDATA 2byte]'''
        
        '''
        That is: if the current time is 8:00:00 on January 1, 2022, the set value is 1641024000, and the hexadecimal representation is 0x61D00A00. 
        In the communication protocol, the low bit comes first and the high bit comes after, then it is 0x00, 0x0A, 0xD0 , 0x61 four bytes.
        Notice! The UNIX timestamp directly read by most programming languages has the local time zone, which needs to be processed. For example, Beijing 
        time in East Eighth District needs to add 28800 to the local UNIX timestamp.
        '''
        
        # Convert hex to decimal now
        self.serial_nb = data_cnt[:2]
        self.time = data_cnt[2:10] 

        self.status = data_cnt[10:12]
        print("Decimal status: ", self.convert_hex_decimal(self.status))
        self.heart_rate = data_cnt[12:14]
        self.respi_rate = data_cnt[14:16]
        self.sdata = data_cnt[16:20]
        self.pdata = data_cnt[20:24]
        print('SDATA-PDATA: ', self.sdata, self.pdata)
        # revert SDATA, PDATA high-low bit
        self.sdata = self.revert_bit_low_high(self.sdata)
        self.pdata = self.revert_bit_low_high(self.pdata)
        
        # Time current from OrangePi
        dict_data_Hex_content = {'serial_number':self.serial_nb, 'Date': time.strftime("%d/%m/%Y"),
                                'Time': time.strftime("%H:%M:%S"), 'Status': self.status,
                                'Heart_rate': self.heart_rate, 'Respiraton_rate': self.respi_rate, 
                                'SDATA':self.sdata, 'PDATA': self.pdata}
        print("Data content hex: ", dict_data_Hex_content)
        
        dict_data_Decimal_content = {'serial_number':self.convert_hex_decimal(self.serial_nb),
                                      'Date': time.strftime("%d/%m/%Y"),
                                      'Time': time.strftime("%H:%M:%S"),             
                                      'Status': self.data_status_define[int(self.convert_hex_decimal(self.status))-1], # get real status
                                      'Heart_rate': self.convert_hex_decimal(self.heart_rate), 
                                      'Respiraton_rate': self.convert_hex_decimal(self.respi_rate)/10,
                                      'SDATA':self.convert_hex_decimal(self.sdata),
                                      'PDATA': self.convert_hex_decimal(self.pdata)}
        print("Data content Decimal: ", dict_data_Decimal_content)
        
        ################ Save data 0x85 to CSV #############################
        self.save_data_to_csv_top(dict_data_Decimal_content, 'data_0x85.csv')
        
        ########################### PUSH data on HA ###################################
        
        self.push_all_data_0x85_HA(dict_data_Decimal_content)
        
        return dict_data_Hex_content, dict_data_Decimal_content
    
    # heart_rate, respiration_rate, snoreData, pressureData, status_in_bed
    def push_all_data_0x85_HA(self, dict_data_Decimal_content):
        # Heart rate
        self.push_data_0x85_HA("heart_rate", 
                               dict_data_Decimal_content['Heart_rate'],
                               self.ip_local)
        
        # Respiration rate
        self.push_data_0x85_HA("respiration_rate",
                               dict_data_Decimal_content['Respiraton_rate'],
                               self.ip_local)
        
        
        
        # status in bed
        self.push_status_0x85_HA("status", 
                               dict_data_Decimal_content['Status'],
                               self.ip_local)
    
    def push_data_0x85_HA(self, name_data, value_data, ip_local_OrangePi):
        self.url_data = f'http://{ip_local_OrangePi}:8123/api/states/Sleeppad.{name_data}'
        if "heart" in name_data:
            unit = "bmp"
        elif "respi" in name_data:
            unit =  "breaths/min"
        
        
        
        headers = {
            'Authorization': f'Bearer {self.HA_TOKEN}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'state': value_data,
            'attributes': {
                'unit_of_measurement': f'{unit}',
                'friendly_name': f'Sleeppad {name_data}',
            }
        }
           
        response = requests.post(self.url_data, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("Dữ liệu đã được gửi lên Home Assistant.")
        else:
            print(f"Đã có lỗi: {response.status_code} - {response.text}")
    
    def push_status_0x85_HA(self, name_data, value_data, ip_local_OrangePi):
        self.url_data = f'http://{ip_local_OrangePi}:8123/api/states/Sleeppad.{name_data}'
        headers = {
            'Authorization': f'Bearer {self.HA_TOKEN}',
            'Content-Type': 'application/json',
        }
        payload = {
            'state': value_data,
            'attributes': {
                'friendly_name': f'Sleeppad {name_data}',
            }
        }
        
        response = requests.post(self.url_data, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("Dữ liệu đã được gửi lên Home Assistant.")
        else:
            print(f"Đã có lỗi: {response.status_code} - {response.text}")

    

    def save_data_to_csv_top(self, dict_data_Decimal_content, file_path):
        """
        Save file data_0x85.csv.
        """
        if file_path == self.file_save_0x85:
            if not os.path.isfile(file_path):
                with open(file_path, "w", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow(["Date", "Time", "Status", "Heart Rate", "Respiration Rate", "SDATA", "PDATA"])

            # Đọc nội dung hiện tại của file
            with open(file_path, "r") as file:
                reader = csv.reader(file)
                data = list(reader)

            # Thêm dữ liệu mới vào đầu file
            data.insert(0, [
                dict_data_Decimal_content["Date"],
                dict_data_Decimal_content["Time"],
                dict_data_Decimal_content["Status"],
                dict_data_Decimal_content["Heart_rate"],
                dict_data_Decimal_content["Respiraton_rate"],
                dict_data_Decimal_content["SDATA"],
                dict_data_Decimal_content["PDATA"]
            ])

            # Ghi lại nội dung mới vào file
            with open(file_path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerows(data)
            print("Save successfull")
        else:
            print("Save failed")
        

    def convert_hex_decimal_apair(self, data_hex): # ID_total
        # Split the hex string into pairs of characters
        pairs = [data_hex[i:i+2] for i in range(0, len(data_hex), 2)]

        # Convert each hex pair to decimal and print the result
        decimal_values = [int(pair, 16) for pair in pairs]
        str_decimal_apair = ''
        for vl in decimal_values:
            str_decimal_apair += str(vl)
        print(str_decimal_apair)
        return str_decimal_apair
    
    def convert_hex_decimal(self, data_hex):
        '''Convert hex to decimal in content: data/response'''
        '0x39-> 39 (hex) - > 3*16^1 + 9*16^0'
        decimal_number = int(data_hex, 16)
        return decimal_number
    
    def revert_bit_low_high(self, data_hex):
        rv_data_hex = ''
        for i in range (len(data_hex)-1, -1, -2):
            rv_data_hex += f'{data_hex[i-1]}{data_hex[i]}'
        return rv_data_hex    
    
if __name__ == '__main__':
    obj_Sleeppad =  class_Collect_Data_Sleeppad('/dev/ttyS4')
    obj_Sleeppad.collect_data_sleeppad()