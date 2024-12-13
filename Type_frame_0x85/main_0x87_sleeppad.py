import time
import csv
import os
import requests

def analyze_content_0x87(data_cnt):
    define_mode = ['Stands for standby mode', 'Stands for server monitoring mode', 'Stands for data debugging mode',
               'Stands for BLE debugging mode', 'Waiting for firmware update']
    define_error = ['No error', 'The device is faulty and must to be returned to the factory']
    
    time_current = time.strftime("%H:%M:%S")
    day_current = time.strftime("%d/%m/%Y")
    mode_hex = data_cnt[0:2]
    error_hex = data_cnt[2:4]
    
    mode_real = convert_mode_0x87(mode_hex, define_mode)
    error_real = convert_error_0x87(error_hex, define_error)
    dict_data_real = {'Date':day_current, 'Time':time_current, 'Mode':mode_real, 'Error':error_real}
    
    ############################# Save data 0x87 to csv ########################
    save_data_0x87('data0x87.csv', dict_data_real)
    return dict_data_real
    

def convert_mode_0x87(data_hex_mode, data_mode_define_0x87):
    all_mode_hex = ['00', '20', '30', '40', 'F0']
    for i in range(0, len(all_mode_hex)):
        if data_hex_mode == all_mode_hex[i]:
            return data_mode_define_0x87[i]

def convert_error_0x87(data_hex_error, data_error_define_0x87):
    if data_hex_error == '00':
        return data_error_define_0x87[0]
    else:
        return data_error_define_0x87[1]

def save_data_0x87(file_path, dict_data_Decimal_content):
    list_label_column = list(dict_data_Decimal_content.keys)
    
    if not os.path.isfile(file_path):
        with open(file_path, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(list_label_column)

    # Đọc nội dung hiện tại của file
    with open(file_path, "r") as file:
        reader = csv.reader(file)
        data = list(reader)
    list_data_insert = []
    for key in list_label_column:
        list_data_insert.append(dict_data_Decimal_content[key])
            
    # Thêm dữ liệu mới vào đầu file
    data.insert(0, list_data_insert)
    # Ghi lại nội dung mới vào file
    with open(file_path, "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerows(data)
    print("Save successfull")

def push_data_0x87_HA(name_data, value_data, ip_local_OrangePi, HA_TOKEN):
        url_data = f'http://{ip_local_OrangePi}:8123/api/states/Sleeppad.{name_data}'
        headers = {
            'Authorization': f'Bearer {HA_TOKEN}',
            'Content-Type': 'application/json',
        }
        payload = {
            'state': value_data,
            'attributes': {
                'friendly_name': f'Sleeppad {name_data}',
            }
        }
        
        response = requests.post(url_data, headers=headers, json=payload)
        
        if response.status_code == 200:
            print("Dữ liệu đã được gửi lên Home Assistant.")
        else:
            print(f"Đã có lỗi: {response.status_code} - {response.text}")