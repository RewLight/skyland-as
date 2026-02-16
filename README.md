# skyland-as

Original Repo: https://gitee.com/FancyCabbage/skyland-auto-sign

森空岛自动签到脚本，支持明日方舟和终末地的自动签到。

> [!INFO]
> **获取 TOKEN 教程**：请前往 [https://gitee.com/FancyCabbage/skyland-auto-sign](https://gitee.com/FancyCabbage/skyland-auto-sign) 查看详细步骤，获取森空岛账号的 TOKEN 后根据配置方式填写。


## 配置方式

### 1. 配置文件 (推荐)

创建 `skyland-as.json` 文件，格式如下：

```json
{
  "accounts": [
    {
      "token": "你的token",
      "games": ["arknights", "endfield"]
    },
    {
      "token": "另一个账号的token",
      "games": ["arknights"]
    }
  ]
}
```

- `token`: 森空岛账号的token，必填
- `games`: 要签到的游戏列表，可选，默认全部游戏
  - `arknights`: 明日方舟
  - `endfield`: 终末地

### 2. 环境变量

设置 `TOKEN` 环境变量，多个token用逗号分隔：

```bash
export TOKEN="token1,token2"
```

**注意**：环境变量中的token会签到所有游戏，无法指定游戏类型。

## 推送配置

### 1. 配置文件方式 (推荐)

在 `skyland-as.json` 文件中配置推送服务：

```json
{
  "push": {
    "services": ["serverchan3", "pushplus"],
    "serverchan3": {
      "sendkey": "你的sendkey",
      "uid": "你的uid"
    },
    "pushplus": {
      "token": "你的token",
      "title": "自定义标题",
      "topic": "群组名称"
    },
    "qmsg": {
      "token": "你的token",
      "qq": "123456789",
      "bot": "123456789",
      "type": "jsend"
    }
  }
}
```

- `services`: 要使用的推送服务列表，未指定时默认全部跳过
- `serverchan3`: Server酱³ 配置
- `pushplus`: PushPlus 配置
- `qmsg`: QMSG 配置

### 2. 环境变量方式

```bash
# 推送服务选择
export PUSH_SERVICES="serverchan3,pushplus"

# Server酱³
export SC3_SENDKEY="你的sendkey"
export SC3_UID="你的uid"  # 可选，若不设将自动从sendkey提取

# PushPlus
export PUSHPLUS_TOKEN="你的token"
export TITLE="自定义标题"  # 可选
export TOPIC="群组名称"  # 可选

# QMSG
export QMSG_TOKEN="你的token"
export QQ="123456789"  # 可选，接收消息的QQ号
export BOT="123456789"  # 可选，机器人QQ号
export QMSG_TYPE="jsend"  # 可选，jsend(私聊)或jgroup(群聊)
```

**注意**：环境变量优先于配置文件

