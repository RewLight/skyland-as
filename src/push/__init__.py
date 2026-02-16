import json
import logging
import os
from configparser import ConfigParser
from .serverchan3 import push_serverchan3
from .pushplus import push_pushplus
from .qmsg import push_qmsg

def load_config_to_env():
    """从配置文件加载配置到环境变量，环境变量优先于配置文件"""
    # 1. 尝试从项目根目录的skyland-as.json文件加载配置
    json_config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'skyland-as.json')
    if os.path.exists(json_config_path):
        try:
            with open(json_config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if 'push' in data:
                    push_config = data['push']
                    
                    # 加载推送服务列表
                    if 'services' in push_config:
                        services = push_config['services']
                        if services and 'PUSH_SERVICES' not in os.environ:
                            os.environ['PUSH_SERVICES'] = ','.join(services)
                    
                    # 加载serverchan3配置
                    if 'serverchan3' in push_config:
                        sc3_config = push_config['serverchan3']
                        if sc3_config.get('sendkey') and 'SC3_SENDKEY' not in os.environ:
                            os.environ['SC3_SENDKEY'] = sc3_config['sendkey']
                        if sc3_config.get('uid') and 'SC3_UID' not in os.environ:
                            os.environ['SC3_UID'] = sc3_config['uid']
                    
                    # 加载pushplus配置
                    if 'pushplus' in push_config:
                        pp_config = push_config['pushplus']
                        if pp_config.get('token') and 'PUSHPLUS_TOKEN' not in os.environ:
                            os.environ['PUSHPLUS_TOKEN'] = pp_config['token']
                        if pp_config.get('title') and 'TITLE' not in os.environ:
                            os.environ['TITLE'] = pp_config['title']
                        if pp_config.get('topic') and 'TOPIC' not in os.environ:
                            os.environ['TOPIC'] = pp_config['topic']
                    
                    # 加载qmsg配置
                    if 'qmsg' in push_config:
                        qmsg_config = push_config['qmsg']
                        if qmsg_config.get('token') and 'QMSG_TOKEN' not in os.environ:
                            os.environ['QMSG_TOKEN'] = qmsg_config['token']
                        if qmsg_config.get('qq') and 'QQ' not in os.environ:
                            os.environ['QQ'] = qmsg_config['qq']
                        if qmsg_config.get('bot') and 'BOT' not in os.environ:
                            os.environ['BOT'] = qmsg_config['bot']
                        if qmsg_config.get('type') and 'QMSG_TYPE' not in os.environ:
                            os.environ['QMSG_TYPE'] = qmsg_config['type']
            logging.info("从 skyland-as.json 加载推送配置成功")
        except Exception as e:
            logging.error(f"从 skyland-as.json 加载推送配置失败: {str(e)}")
    
    # 2. 尝试从同目录下的config.ini文件加载配置（向后兼容）
    config = ConfigParser()
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if os.path.exists(config_path):
        try:
            config.read(config_path, encoding='utf-8')
            
            # 遍历配置文件中的所有section和option，添加到环境变量
            for section_name in config.sections():
                for option in config.options(section_name):
                    value = config.get(section_name, option)
                    # 将配置项添加到环境变量中，仅当环境变量不存在时
                    env_key = option.upper()  # 转换为大写作为环境变量名
                    if value and env_key not in os.environ:  # 环境变量优先
                        os.environ[env_key] = value
            logging.info("从 config.ini 加载推送配置成功")
        except Exception as e:
            logging.error(f"从 config.ini 加载推送配置失败: {str(e)}")

# 加载配置到环境变量
load_config_to_env()

__available_pusher = {
    'serverchan3': push_serverchan3,
    'pushplus': push_pushplus,
    'QMSG': push_qmsg,
}


def push(all_logs: list[str]):
    """
    推送签到结果
    :param all_logs: 签到结果日志列表
    """
    logging.info("开始推送结果")
    
    # 获取用户指定的推送服务，未指定时默认全部跳过
    push_services = os.environ.get('PUSH_SERVICES', '').strip()
    selected_services = []
    
    if push_services:
        # 解析用户指定的推送服务
        for service in push_services.split(','):
            service = service.strip()
            if service in __available_pusher:
                selected_services.append(service)
            else:
                logging.warning(f"未知的推送服务: {service}")
    else:
        # 未指定推送服务时，默认全部跳过
        logging.info("未指定推送服务，跳过推送")
        logging.info("推送结束")
        return
    
    if not selected_services:
        logging.warning("没有可用的推送服务")
        logging.info("推送结束")
        return
    
    logging.info(f"将使用以下推送服务: {', '.join(selected_services)}")
    
    # 记录实际推送的服务数量
    pushed_services = []
    
    for service in selected_services:
        try:
            # 推送服务函数会在未配置时直接返回，不会抛出异常
            __available_pusher[service](all_logs)
            # 只有在函数执行完成后才认为推送成功
            # 但实际推送成功的判断由各个服务函数内部处理
        except Exception as e:
            logging.error(f"[Push] {service}时出现问题", exc_info=e)
    
    logging.info("推送结束")
