import logging
import requests
import json
import time
import os
from login.login import CampusCard


class Sign(CampusCard):
    def __init__(self, phone, password):
        super().__init__(phone, password)
        self.initLogging()
        post_json = self.get_post_json()
        self.note = self.healthy_check_in(post_json)


    @staticmethod
    def initLogging():
        logging.getLogger().setLevel(logging.INFO)
        logging.basicConfig(format="[%(levelname)s]; %(message)s")

    def get_post_json(self):
        """
        获取打卡数据
        """
        post_json = {
            "jsonData": {
                "templateid": "pneumonia",
                "token": self.user_info['sessionId']
            },
            "businessType": "epmpics",
            "method": "userComeApp"
        }
        for _ in range(3):
            try:
                res = requests.post(
                    url="https://reportedh5.17wanxiao.com/sass/api/epmpics",
                    json=post_json,
                    timeout=10,
                ).json()
            except:
                logging.warning("获取完美校园打卡post参数失败，正在重试...")
                continue
            if res["code"] != "10000":
                logging.warning(res)
            data = json.loads(res["data"])
            # print(data)
            post_dict = {
                "areaStr": data['areaStr'],
                "deptStr": data['deptStr'],
                "deptid": data['deptStr']['deptid'] if data['deptStr'] else None,
                "customerid": data['customerid'],
                "userid": data['userid'],
                "username": data['username'],
                "stuNo": data['stuNo'],
                "phonenum": data["phonenum"],
                "templateid": data["templateid"],
                "updatainfo": [
                    {"propertyname": i["propertyname"], "value": i["value"]}
                    for i in data["cusTemplateRelations"]
                ],
                "updatainfo_detail": [
                    {
                        "propertyname": i["propertyname"],
                        "checkValues": i["checkValues"],
                        "description": i["decription"],
                        "value": i["value"],
                    }
                    for i in data["cusTemplateRelations"]
                ],
                "checkbox": [
                    {"description": i["decription"], "value": i["value"]}
                    for i in data["cusTemplateRelations"]
                ],
            }
            # print(json.dumps(post_dict, sort_keys=True, indent=4, ensure_ascii=False))
            logging.info("获取完美校园打卡post参数成功")
            return post_dict
        return None

    def healthy_check_in(self, post_dict):
        """
        提交打卡数据
        """
        check_json = {
            "businessType": "epmpics",
            "method": "submitUpInfo",
            "jsonData": {
                "deptStr": post_dict["deptStr"],
                "areaStr": post_dict["areaStr"],
                "reportdate": round(time.time() * 1000),
                "customerid": post_dict["customerid"],
                "deptid": post_dict["deptid"],
                "source": "app",
                "templateid": post_dict["templateid"],
                "stuNo": post_dict["stuNo"],
                "username": post_dict["username"],
                "phonenum": self.phone,
                "userid": post_dict["userid"],
                "updatainfo": post_dict["updatainfo"],
                "gpsType": 1,
                "token": self.user_info['sessionId'],
            },
        }
        for _ in range(3):
            try:
                res = requests.post(
                    "https://reportedh5.17wanxiao.com/sass/api/epmpics", json=check_json
                ).json()
                if res['code'] == '10000':
                    logging.info(res)
                    return {
                        "status": 1,
                        "res": res,
                        "post_dict": post_dict,
                        "check_json": check_json,
                        "type": "healthy",
                    }
                elif "频繁" in res['data']:
                    logging.info(res)
                    return {
                        "status": 1,
                        "res": res,
                        "post_dict": post_dict,
                        "check_json": check_json,
                        "type": "healthy",
                    }
                else:
                    logging.warning(res)
                    return {"status": 0, "errmsg": f"{post_dict['username']}: {res}"}
            except:
                errmsg = f"```打卡请求出错```"
                logging.warning("健康打卡请求出错")
                return {"status": 0, "errmsg": errmsg}
        return {"status": 0, "errmsg": "健康打卡请求出错"}


if __name__ == '__main__':
    sign = Sign('用户名手机号', '密码')
    with open(os.path.join(sign.dir_path + '/../log.txt'), 'w+') as f:
        f.write(sign.note['res']['msg'])
