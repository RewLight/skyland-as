import json
import logging
import os
from datetime import date

import requests


def push_qmsg(all_logs: list[str]):
    """
    QMSG 推送
    通过环境变量控制：
      QMSG_TOKEN: 必填
      QQ: 可选，指定要接收消息的QQ号或者QQ群。多个以英文逗号分割，例如：12345,12346。
      BOT： 可选，机器人的QQ号。
      QMSG_TYPE: 可选，推送类型，默认私聊 (jsend)，可选群聊 (jgroup)
    :param all_logs: 签到结果日志列表
    """
    # 获取配置
    token = os.environ.get('QMSG_TOKEN', '').strip()
    if not token:
        logging.info("未设置 QMSG_TOKEN，跳过 QMSG 推送")
        return
    
    qq = os.environ.get('QQ', '').strip()
    bot = os.environ.get('BOT', '').strip()
    qmsg_type = os.environ.get('QMSG_TYPE', 'jsend').strip()  # jsend 私聊, jgroup 群聊
    
    # 验证推送类型
    if qmsg_type not in ['jsend', 'jgroup']:
        logging.warning(f"未知的 QMSG_TYPE: {qmsg_type}，将使用默认值 jsend")
        qmsg_type = 'jsend'

    title = f'森空岛自动签到结果 - {date.today().strftime("%Y-%m-%d")}'
    desp = '\n'.join(all_logs) if all_logs else '今日无可用账号或无输出'
    
    # 构建API地址和请求参数
    api = f"https://qmsg.zendee.cn/{qmsg_type}/{token}"
    payload = {
        "msg": f"{title}\n{desp}",
    }
    
    # 添加可选参数
    if qq:
        payload["qq"] = qq
    if bot:
        payload["bot"] = bot

    # 发送请求
    try:
        response = requests.post(api, json=payload, timeout=10)
        if response.status_code == 200:
            # 尝试解析响应
            try:
                result = response.json()
                if result.get('code') == 0:
                    logging.info("QMSG 推送成功")
                else:
                    logging.error(f"QMSG 推送失败: {result.get('reason', '未知错误')}")
            except json.JSONDecodeError:
                logging.warning("QMSG 推送响应不是有效的JSON")
                logging.info("QMSG 推送成功")
        else:
            logging.error(f"QMSG 推送失败，HTTP状态码: {response.status_code}, 响应: {response.text}")
    except requests.RequestException as e:
        logging.error(f"QMSG 推送网络错误", exc_info=e)
    except Exception as e:
        logging.error(f"QMSG 推送未知错误", exc_info=e)