# SecuritySm.py from FancyCabbage/skyland-auto-sign(master#4da03e0) 
# !! Modified
import hashlib
import hmac
import json
import logging
import os.path
import threading
import time
from urllib import parse

import requests

from SecuritySm import get_d_id

app_code = '4ca99fa6b56cc2ba'
token_env = os.environ.get('TOKEN')
config_file_path = 'skyland-as.json'

http_local = threading.local()
header = {
    'cred': '',
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-A5560 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36; SKLand/1.52.1',
    'Accept-Encoding': 'gzip',
    'Connection': 'close',
    'X-Requested-With': 'com.hypergryph.skland'
}
header_login = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 12; SM-A5560 Build/V417IR; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/101.0.4951.61 Safari/537.36; SKLand/1.52.1',
    'Accept-Encoding': 'gzip',
    'Connection': 'close',
    'dId': get_d_id(),
    'X-Requested-With': 'com.hypergryph.skland'
}

# 签名请求头一定要这个顺序，否则失败
# timestamp是必填的,其它三个随便填,不要为none即可
header_for_sign = {
    'platform': '3',
    'timestamp': '',
    'dId': header_login['dId'],
    'vName': '1.0.0'
}

# 签到url
sign_url_mapping = {
    'arknights': 'https://zonai.skland.com/api/v1/game/attendance',
    'endfield': 'https://zonai.skland.com/web/v1/game/endfield/attendance'
}

# 绑定的角色url
binding_url = "https://zonai.skland.com/api/v1/game/player/binding"
# 使用token获得认证代码
grant_code_url = "https://as.hypergryph.com/user/oauth2/v2/grant"
# 使用认证代码获得cred
cred_code_url = "https://zonai.skland.com/web/v1/user/auth/generate_cred_by_code"
# refresh
refresh_token_url = "https://zonai.skland.com/web/v1/auth/refresh"


def generate_signature(path, body_or_query):
    """
    获得签名头
    接口地址+方法为Get请求？用query否则用body+时间戳+ 请求头的四个重要参数（dId，platform，timestamp，vName）.toJSON()
    将此字符串做HMAC加密，算法为SHA-256，密钥token为请求cred接口会返回的一个token值
    再将加密后的字符串做MD5即得到sign
    :param path: 请求路径（不包括网址）
    :param body_or_query: 如果是GET，则是它的query。POST则为它的body
    :return: 计算完毕的sign
    """
    # 总是说请勿修改设备时间，怕不是yj你的服务器有问题吧，所以这里特地-2
    t = str(int(time.time()) - 2)
    token = http_local.token.encode('utf-8')
    header_ca = json.loads(json.dumps(header_for_sign))
    header_ca['timestamp'] = t
    header_ca_str = json.dumps(header_ca, separators=(',', ':'))
    s = path + body_or_query + t + header_ca_str
    hex_s = hmac.new(token, s.encode('utf-8'), hashlib.sha256).hexdigest()
    md5 = hashlib.md5(hex_s.encode('utf-8')).hexdigest().encode('utf-8').decode('utf-8')
    logging.info(f'算出签名: {md5}')
    return md5, header_ca


def get_sign_header(url: str, method, body, h):
    p = parse.urlparse(url)
    if method.lower() == 'get':
        h['sign'], header_ca = generate_signature(p.path, p.query)
    else:
        h['sign'], header_ca = generate_signature(p.path, json.dumps(body) if body is not None else '')
    for i in header_ca:
        h[i] = header_ca[i]
    return h


def parse_user_token(t):
    try:
        t = json.loads(t)
        return t['data']['content']
    except:
        pass
    return t


def get_cred_by_token(token):
    grant_code = get_grant_code(token)
    return get_cred(grant_code)


def get_grant_code(token):
    response = requests.post(grant_code_url, json={
        'appCode': app_code,
        'token': token,
        'type': 0
    }, headers=header_login)
    resp = response.json()
    if response.status_code != 200:
        raise Exception(f'获得认证代码失败：{resp}')
    if resp.get('status') != 0:
        raise Exception(f'获得认证代码失败：{resp["msg"]}')
    return resp['data']['code']


def get_cred(grant):
    resp = requests.post(cred_code_url, json={
        'code': grant,
        'kind': 1
    }, headers=header_login).json()
    if resp['code'] != 0:
        raise Exception(f'获得cred失败：{resp["message"]}')
    return resp['data']


def refresh_token():
    headers = get_sign_header(refresh_token_url, 'get', None, http_local.header)
    resp = requests.get(refresh_token_url, headers=headers).json()
    if resp.get('code') != 0:
        raise Exception(f'刷新token失败:{resp["message"]}')
    http_local.token = resp['data']['token']


def get_binding_list():
    v = []
    resp = requests.get(binding_url, headers=get_sign_header(binding_url, 'get', None, http_local.header)).json()

    if resp['code'] != 0:
        logging.error(f"请求角色列表出现问题：{resp['message']}")
        if resp.get('message') == '用户未登录':
            logging.error(f'用户登录可能失效了，请检查token是否正确！')
            return []
    for i in resp['data']['list']:
        # 也许有些游戏没有签到功能？
        if i.get('appCode') not in ('arknights', 'endfield'):
            continue
        for j in i.get('bindingList'):
            j['appCode'] = i['appCode']
        v.extend(i['bindingList'])
    return v


def sign_for_arknights(data: dict):
    # 返回是否成功，消息
    body = {
        'gameId': data.get('gameId'),
        'uid': data.get('uid')
    }
    url = sign_url_mapping['arknights']
    headers = get_sign_header(url, 'post', body, http_local.header)
    resp = requests.post(url, headers=headers, json=body).json()
    game_name = data.get('gameName')
    channel = data.get("channelName")
    nickname = data.get('nickName') or ''
    if resp.get('code') != 0:
        return [
            f'[{game_name}]角色{nickname}({channel})签到失败了！原因：{resp["message"]}']
    result = ''
    awards = resp['data']['awards']
    for j in awards:
        res = j['resource']
        result += f'{res["name"]}×{j.get("count") or 1}'
    return [f'[{game_name}]角色{nickname}({channel})签到成功，获得了{result}']


def sign_for_endfield(data: dict):
    roles: list[dict] = data.get('roles')
    game_name = data.get('gameName')
    channel = data.get("channelName")
    result = []
    for i in roles:
        nickname = i.get('nickname') or ''
        resp = do_sign_for_endfield(i)
        j = resp.json()
        if j['code'] != 0:
            result.append(f'[{game_name}]角色{nickname}({channel})签到失败了！原因:{j["message"]}')
        else:
            awards_result = []
            result_data: dict = j['data']
            result_info_map: dict = result_data['resourceInfoMap']
            for a in result_data['awardIds']:
                award_id = a['id']
                awards = result_info_map[award_id]
                award_name = awards['name']
                award_count = awards['count']
                awards_result.append(f'{award_name}×{award_count}')

            result.append(f'[{game_name}]角色{nickname}({channel})签到成功，获得了:{",".join(awards_result)}')
    return result


def do_sign_for_endfield(role: dict):
    url = sign_url_mapping['endfield']
    headers = get_sign_header(url, 'post', None, http_local.header)
    headers.update({
        'Content-Type': 'application/json',
        # FIXME b服不知道是不是这样
        # gameid_roleid_serverid
        'sk-game-role': f'3_{role["roleId"]}_{role["serverId"]}',
        'referer': 'https://game.skland.com/',
        'origin': 'https://game.skland.com/'
    })
    return requests.post(url, headers=headers)


def do_sign(cred_resp, games=None):
    """
    执行签到
    :param cred_resp: 认证响应，包含token和cred
    :param games: 要签到的游戏列表，默认全部游戏
    :return: (是否成功, 签到日志列表)
    """
    http_local.token = cred_resp['token']
    http_local.header = header.copy()
    http_local.header['cred'] = cred_resp['cred']
    characters = get_binding_list()
    success = True
    logs_out = []  # 新增：用于 Server酱³ 的汇总文本
    
    # 默认签到所有游戏
    if games is None:
        games = ['arknights', 'endfield']
    
    for i in characters:
        app_code = i['appCode']
        # 检查是否需要签到该游戏
        if app_code not in games:
            logging.info(f'跳过游戏 {app_code} 的签到')
            continue
        
        msg = None
        if app_code == 'arknights':
            msg = sign_for_arknights(i)
        elif app_code == 'endfield':
            msg = sign_for_endfield(i)
        logging.info(msg)

        logs_out.extend(msg)

    return success, logs_out





def read_from_file():
    """
    从配置文件读取账号信息
    :return: 账号信息列表，每个元素包含token和games字段
    """
    v = []
    if not os.path.exists(config_file_path):
        logging.warning(f'配置文件 {config_file_path} 不存在，将从环境变量读取token')
        return v
    
    try:
        with open(config_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'accounts' in data:
                for account in data['accounts']:
                    token = account.get('token', '').strip()
                    if token:
                        # 处理游戏配置，默认为全部游戏
                        games = account.get('games', ['arknights', 'endfield'])
                        # 验证游戏类型
                        valid_games = []
                        for game in games:
                            if game in sign_url_mapping:
                                valid_games.append(game)
                            else:
                                logging.warning(f'未知的游戏类型: {game}，将被忽略')
                        if not valid_games:
                            # 如果没有有效的游戏类型，默认全部游戏
                            valid_games = ['arknights', 'endfield']
                        v.append({
                            'token': parse_user_token(token),
                            'games': valid_games
                        })
        logging.info(f'从配置文件中读取到{len(v)}个账号...')
    except Exception as e:
        logging.error(f'读取配置文件失败：{str(e)}')
    
    return v


def read_from_env():
    """
    从环境变量读取账号信息
    :return: 账号信息列表，每个元素包含token和games字段
    """
    v = []
    if token_env:
        token_list = token_env.split(',')
        for i in token_list:
            i = i.strip()
            if i:
                # 环境变量中的token默认签到所有游戏
                v.append({
                    'token': parse_user_token(i),
                    'games': ['arknights', 'endfield']
                })
        logging.info(f'从环境变量中读取到{len(v)}个账号...')
    return v


def init_token():
    """
    初始化账号信息，优先从环境变量读取，其次从配置文件读取
    :return: 账号信息列表，每个元素包含token和games字段
    """
    # 优先从环境变量读取
    accounts = read_from_env()
    if accounts:
        return accounts
    
    # 环境变量不存在时，从配置文件读取
    accounts = read_from_file()
    if accounts:
        return accounts
    
    # 没有找到账号信息，抛出异常
    raise Exception('未找到账号信息，请在环境变量中设置TOKEN或在配置文件中添加账号')


def start():
    accounts = init_token()
    success = True
    all_logs = []  # 新增：汇总所有账号/角色的输出
    for account in accounts:
        try:
            token = account.get('token')
            games = account.get('games', ['arknights', 'endfield'])
            logging.info(f'开始处理账号，将签到游戏：{", ".join(games)}')
            sign_success, logs_out = do_sign(get_cred_by_token(token), games)
            all_logs.extend(logs_out)
            if not sign_success:
                success = False
        except Exception as ex:
            err = f'签到失败，原因：{str(ex)}'
            logging.error(err, exc_info=ex)
            all_logs.append(err)
            success = False
    logging.info("签到完成！")

    return success, all_logs
