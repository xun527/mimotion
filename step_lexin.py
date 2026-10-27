#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""乐心健康刷步 - GitHub Actions 版
凭据通过环境变量（GitHub Secrets）读取:
  LEXIN_ACCOUNTS  格式：每行一个账号 "账号,密码"
    例：
    17610827527,Zhang1987
    402914287@qq.com,Zhang1987
"""
import hashlib
import json
import os
import random
import sys
import time

import requests

# 步数范围（随机取值）
STEP_MIN = 30000
STEP_MAX = 39000

# 账号之间提交间隔（秒）
ACCOUNT_INTERVAL = 5


def md5(code):
    return hashlib.md5(code.encode("utf8")).hexdigest()


def login(mobile, password):
    """登录乐心健康，返回 accessToken 和 userId"""
    url = "https://sports.lifesense.com/sessions_service/login?version=4.5&systemType=2"
    headers = {
        'Content-Type': 'application/json; charset=utf-8',
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-G9500 Build/PPR1.180610.011)"
    }
    datas = {
        "appType": 6,
        "clientId": "8e844e28db7245eb81823132464835eb",
        "loginName": str(mobile),
        "password": md5(str(password)),
        "roleType": 0
    }
    r = requests.post(url, headers=headers, data=json.dumps(datas), timeout=15)
    res = r.json()
    data = res.get("data") or {}
    if not data.get("accessToken"):
        raise RuntimeError(f"登录失败: {res.get('msg') or res.get('errorMsg')}")
    return data["accessToken"], data["userId"]


def upload_step(accessToken, userId, step):
    """上传步数"""
    url = "https://sports.lifesense.com/sport_service/sport/sport/uploadMobileStepV2?version=4.5&systemType=2"
    timeStamp = time.time()
    strTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timeStamp))
    measureTime = strTime + "," + str(int(timeStamp))
    headers = {
        'Cookie': 'accessToken=' + accessToken,
        'Content-Type': 'application/json; charset=utf-8',
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 9; SM-G9500 Build/PPR1.180610.011)"
    }
    sport_datas = {
        "list": [
            {
                "DataSource": 2,
                "calories": str(int(step / 4)),
                "deviceId": "M_NULL",
                "distance": str(int(step / 3)),
                "exerciseTime": 0,
                "isUpload": 0,
                "measurementTime": measureTime,
                "step": str(step),
                "type": 2,
                "updated": str(int(timeStamp * 1000)),
                "userId": str(userId)
            }
        ]
    }
    result = requests.post(url, headers=headers, data=json.dumps(sport_datas), timeout=15)
    return json.loads(result.text).get("msg")


def run_account(user, password):
    step = random.randint(STEP_MIN, STEP_MAX)
    try:
        accessToken, userId = login(user, password)
        msg = upload_step(accessToken, userId, step)
        if msg == "成功":
            print(f"账号 {user[:3]}**** 刷步成功: {step} 步")
            return True
        print(f"账号 {user[:3]}**** 刷步失败: {msg} (步数 {step})")
    except Exception as e:
        print(f"账号 {user[:3]}**** 异常: {e}")
    return False


def main():
    raw = os.environ.get('LEXIN_ACCOUNTS', '')
    accounts = []
    for line in raw.strip().splitlines():
        line = line.strip()
        if line and ',' in line:
            user, pwd = line.split(',', 1)
            accounts.append((user.strip(), pwd.strip()))
    if not accounts:
        print("未配置 LEXIN_ACCOUNTS，退出")
        sys.exit(1)

    print(f"[{time.strftime('%F %T')}] 乐心健康刷步启动，共 {len(accounts)} 个账号")
    ok_count = 0
    for i, (user, password) in enumerate(accounts, 1):
        if run_account(user, password):
            ok_count += 1
        if i < len(accounts):
            time.sleep(ACCOUNT_INTERVAL)

    print(f"[{time.strftime('%F %T')}] 执行完毕: 成功 {ok_count}/{len(accounts)}")
    if ok_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
