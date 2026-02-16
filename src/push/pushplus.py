import json
import logging
import os
from datetime import date

import requests


def push_pushplus(all_logs: list[str]):
    """
    PushPlus 推送
    通过环境变量控制：
      PUSHPLUS_TOKEN: 推送密钥，必填
      TITLE：标题（可选）
      TOPIC：群组（可选）
    :param all_logs: 签到结果日志列表
    """
    # 获取配置
    token = os.environ.get('PUSHPLUS_TOKEN', '').strip()
    if not token:
        logging.info("未设置 PUSHPLUS_TOKEN，跳过 PushPlus 推送")
        return
    
    title = os.environ.get('TITLE', f'森空岛自动签到结果 - {date.today().strftime("%Y-%m-%d")}')
    topic = os.environ.get('TOPIC', '').strip()
    desp = '\n'.join(all_logs) if all_logs else '今日无可用账号或无输出'

    # 构建API地址和请求参数
    api = "https://www.pushplus.plus/send"
    payload = {
        "token": token,
        "title": title or "通知",
        "content": desp or "",
        "template": "txt"
    }
    
    if topic:
        payload["topic"] = topic

    # 发送请求
    try:
        response = requests.post(api, json=payload, timeout=10)
        if response.status_code == 200:
            # 尝试解析响应
            try:
                result = response.json()
                if result.get('code') == 200:
                    logging.info("PushPlus 推送成功")
                else:
                    logging.error(f"PushPlus 推送失败: {result.get('msg', '未知错误')}")
            except json.JSONDecodeError:
                logging.warning("PushPlus 推送响应不是有效的JSON")
                logging.info("PushPlus 推送成功")
        else:
            logging.error(f"PushPlus 推送失败，HTTP状态码: {response.status_code}, 响应: {response.text}")
    except requests.RequestException as e:
        logging.error(f"PushPlus 推送网络错误", exc_info=e)
    except Exception as e:
        logging.error(f"PushPlus 推送未知错误", exc_info=e)