import hashlib
import json
import requests
import urllib3
import random
import os
from Encryption_decryption import des_3
from Encryption_decryption import rsa_encrypt as rsa
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CampusCard:
    """
    完美校园模拟登陆系统
    需要信息为手机号与密码
    如果初次运行需要短信验证码
    """
    def __init__(self, phone, password):
        """
        初始化信息，获取手机号码与密码
        读取设备ID号，若没有设备ID号则虚拟新建一个设备ID号，此ID号用于后续密码登陆
        """
        self.phone = phone
        self.password = password
        self.dir_path = os.path.dirname(__file__)
        deviceID_path = os.path.join(self.dir_path + '/../user_info/deviceID.txt')
        with open(deviceID_path, 'r+') as deviceID:
            self.deviceID = deviceID.read()
            if self.deviceID == '':
                new_deviceID = random.randint(000000000000000, 999999999999999)
                deviceID.write(str(new_deviceID))
                self.deviceID = new_deviceID

        rsa_keys = rsa.create_key_pair(1024)
        self.user_info = {
            'appKey': '',
            'sessionId': '',
            'login': False,
            'serverPublicKey': '',
            'deviceId': self.deviceID,
            'wanxiaoVersion': 10535102,
            'rsaKey': {
                'private': rsa_keys[1],
                'public': rsa_keys[0]
            }
        }
        sms_path = os.path.join(self.dir_path + '/../user_info/sms.txt')
        self.sms = open(sms_path, 'r+')
        self.exchange_secret()
        self.login()

    def exchange_secret(self):
        """
        与完美校园服务器交换RSA加密的公钥，并取得sessionId
        """
        resp = requests.post(
            "https://app.17wanxiao.com/campus/cam_iface46/exchangeSecretkey.action",
            headers={
                "User-Agent": "NCP/5.3.5 (iPad; iOS 14.3; Scale/2.00)",
            },
            json={
                "key": self.user_info["rsaKey"]["public"]
            },
            verify=False
        )
        session_info = json.loads(
            rsa.rsa_decrypt(resp.text.encode(resp.apparent_encoding), self.user_info["rsaKey"]["private"])
        )
        self.user_info["sessionId"] = session_info["session"]
        self.user_info["appKey"] = session_info["key"][:24]

    def login(self):
        """
        使用账号密码登录完美校园APP
        """
        password_list = [des_3.des_3_encrypt(self.password, self.user_info["appKey"], "66666666")]
        login_args = {
            "appCode": "M002",
            "deviceId": self.user_info["deviceId"],
            "netWork": "wifi",
            "password": password_list,
            "qudao": "guanwang",
            "requestMethod": "cam_iface46/loginnew.action",
            "shebeixinghao": "iPadPro",
            "systemType": "iOS",
            "telephoneInfo": "14.3",
            "telephoneModel": "iPad",
            "type": "1",
            "userName": self.phone,
            "wanxiaoVersion": 10535102,
            "yunyingshang": "07"
        }
        upload_args = {
            "session": self.user_info["sessionId"],
            "data": des_3.object_encrypt(login_args, self.user_info["appKey"])
        }
        # print(upload_args["data"])
        resp = requests.post(
            "https://app.17wanxiao.com/campus/cam_iface46/loginnew.action",
            headers={"campusSign": hashlib.sha256(json.dumps(upload_args).encode('utf-8')).hexdigest()},
            json=upload_args,
            verify=False
        ).json()
        if resp["result_"]:
            self.user_info["login"] = True
            print(resp['message_'])
        if not resp["result_"]:
            print(resp['message_'])
            print('请将短信验证码保存至user_info文件夹中的sms.txt文件内，并重新运行此程序！')
            self.sendSMS()
            if self.sms.read() != '':
                self.smslogin(int(self.sms.read()))
        return resp["result_"]

    def sendSMS(self):
        """
        发送请求，获取手机验证码
        """
        send = {
            'action': "registAndLogin",
            'deviceId': self.user_info['deviceId'],
            'mobile': self.phone,
            'requestMethod': "cam_iface46/gainMatrixCaptcha.action",
            'type': "sms"
        }
        upload_args = {
            "session": self.user_info["sessionId"],
            "data": des_3.object_encrypt(send, self.user_info["appKey"])
        }
        resp = requests.post(
            "https://app.17wanxiao.com/campus/cam_iface46/gainMatrixCaptcha.action",
            headers={"campusSign": hashlib.sha256(json.dumps(upload_args).encode('utf-8')).hexdigest()},
            json=upload_args,
            verify=False
        ).json()
        return resp["result_"]

    def smslogin(self, sms):
        """
        输入手机的验证码，实现短信验证登陆
        """
        data = {
            'appCode': "M002",
            'deviceId': self.user_info['deviceId'],
            'netWork': "wifi",
            'qudao': "guanwang",
            'requestMethod': "cam_iface46/registerUsersByTelAndLoginNew.action",
            'shebeixinghao': "iPadPro",
            'sms': sms,
            'systemType': "iOS",
            'telephoneInfo': "14.3",
            'telephoneModel': 'iPad',
            'mobile': self.phone,
            'wanxiaoVersion': 10535102
        }
        upload_args = {
            "session": self.user_info["sessionId"],
            "data": des_3.object_encrypt(data, self.user_info["appKey"])
        }
        resp = requests.post(
            "https://app.17wanxiao.com/campus/cam_iface46/registerUsersByTelAndLoginNew.action",
            headers={"campusSign": hashlib.sha256(json.dumps(upload_args).encode('utf-8')).hexdigest()},
            json=upload_args,
            verify=False
        ).json()
        if resp["result_"]:
            self.user_info["login"] = True
            print(resp["message_"])
        else:
            print(resp['message_'])
        return resp["result_"]

    def __del__(self):
        """
        析构函数
        当结束运行时析构
        保存当前获取的user_info数据，储存到user_info.json
        并且重置sms.txt中的验证码数据
        """
        self.sms.truncate()
        self.sms.close()


