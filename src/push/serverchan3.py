import json
import logging
import os
import re
from datetime import date

import requests


def _format_serverchan_desp(all_logs: list[str]) -> str:
    """
    格式化Server酱推送内容
    :param all_logs: 签到结果日志列表
    :return: 格式化后的推送内容
    """
    if not all_logs:
        return '今日无可用账号或无输出'

    lines: list[str] = []
    for item in all_logs:
        text = item.replace('\r\n', '\n')
        parts = text.split('\n\n')
        if not parts:
            lines.append('')
            continue
        lines.extend(parts)

    # Server酱 desp 使用 Markdown，单换行会折叠为一个空格，需要显式换行。
    return '  \n'.join(line.rstrip() for line in lines)


def push_serverchan3(all_logs: list[str]):
    """
    Server酱³ 推送
    通过环境变量控制：
      SC3_SENDKEY: 必填
      SC3_UID: 可选（若不设，将自动从 sendkey 中提取）
    :param all_logs: 签到结果日志列表
    """
    # 获取配置
    sendkey = os.environ.get('SC3_SENDKEY', '').strip()
    if not sendkey:
        logging.info("未设置 SC3_SENDKEY，跳过 Server酱 推送")
        return
    
    uid = os.environ.get('SC3_UID', '').strip() or None
    title = f'森空岛自动签到结果 - {date.today().strftime("%Y-%m-%d")}'

    # 格式化推送内容
    desp = _format_serverchan_desp(all_logs)

    # 提取或使用指定的uid
    if uid is None:
        m = re.match(r"^sctp(\d+)t", sendkey)
        if not m:
            logging.error("无法从 sendkey 中提取 uid，请显式设置 SC3_UID")
            return
        uid = m.group(1)

    # 构建API地址和请求参数
    api = f"https://{uid}.push.ft07.com/send/{sendkey}.send"
    payload = {
        "title": title or "通知",
        "desp": desp or "",
    }

    # 发送请求
    try:
        response = requests.post(api, json=payload, timeout=10)
        if response.status_code == 200:
            # 尝试解析响应
            try:
                result = response.json()
                if result.get('ok') or result.get('code') == 0:
                    logging.info("Server酱 推送成功")
                else:
                    logging.error(f"Server酱 推送失败: {result.get('message', '未知错误')}")
            except json.JSONDecodeError:
                logging.warning("Server酱 推送响应不是有效的JSON")
                logging.info("Server酱 推送成功")
        else:
            logging.error(f"Server酱 推送失败，HTTP状态码: {response.status_code}, 响应: {response.text}")
    except requests.RequestException as e:
        logging.error(f"Server酱 推送网络错误", exc_info=e)
    except Exception as e:
        logging.error(f"Server酱 推送未知错误", exc_info=e)
