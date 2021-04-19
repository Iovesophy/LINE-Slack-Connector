# LINE-Slack-Connector

SlackユーザとLINEユーザを繋げたい。

# Dependency
* Slack
    * Webhook 
    * bots
* LINE
    * LINE Notify
    * LineBotSdk
* Heroku
    * HerokuCLI


# Goal
LINEからSlackへ、SlackからLINEへ双方向でメッセージをやりとりする。

## Directory

```
├── LINE_to_Slack           #好きな名前で良い。
│   ├── Procfile            #デプロイに必要
│   ├── main.py             #本体
│   ├── requirements.txt　　 #デプロイに必要
│   └── runtime.txt　　　　　 #デプロイに必要
├── README.md
└── Slack_to_LINE            #好きな名前で良い。
    ├── Procfile　　　　　　　 #デプロイに必要
    ├── plugins　　　         # botの機能はこのディレクトリに追加する
    │   ├── __init__.py      # モジュールを示すためのファイル。空で良い
    │   └── line_mention.py  # 機能を書き込むファイル。任意の名前で良い
    ├── requirements.txt　　  #デプロイに必要
    ├── run.py               # このプログラムを実行することで、ボットを起動する
    ├── runtime.txt　　　　　  #デプロイに必要
    └── slackbot_settings.py　# botに関する設定を書くファイル
```

# SlackからLINEへ

まずは、SlackからLINEへということを考えたい。
PythonのslackbotライブラリでSlackボットを作りたい。[^1]

## slackbotのインストール
```$
$ sudo apt install python3-pip
$ sudo pip3 install slackbot
```
ディレクトリ構成は以下である。

```bash:Slack_to_LINE
└── Slack_to_LINE            #好きな名前で良い。
    ├── Procfile　　　　　　　 #デプロイに必要
    ├── plugins　　　         # botの機能はこのディレクトリに追加する
    │   ├── __init__.py      # モジュールを示すためのファイル。空で良い
    │   └── line_mention.py  # 機能を書き込むファイル。任意の名前で良い
    ├── requirements.txt　　  #デプロイに必要
    ├── run.py               # このプログラムを実行することで、ボットを起動する
    ├── runtime.txt　　　　　  #デプロイに必要
    └── slackbot_settings.py　# botに関する設定を書くファイル
```

このrun.pyはボットを起動する部分である。

```python:run.py
# coding: utf-8
from slackbot.bot import Bot
def main():
    bot = Bot()
    bot.run()
if __name__ == "__main__":
    main()
```
次にプラグインを書いていこう。
Slackからメッセージを受け取ったらLINE Notifyを使って送信したい。

```sh:LineNotify

$ curl -X POST -H "Authorization: Bearer ここにアクセストークン" -F "message=${code}" https://notify-api.line.me/api/notify

```
slackbot_settings.pyの中身を以下のようにする。

```python:slackbot_setting.py
# coding: utf-8
import os
# トークンを指定
API_TOKEN = os.environ["API_TOKEN"]

# このbot宛の標準の応答メッセージ
DEFAULT_REPLY = ""

# プラグインスクリプトのリスト
PLUGINS = ['plugins']
```
ちなみにプラグインは以下のように書けば良い。


```python:plugins/line_mention.py
# coding: utf-8 -*-
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.bot import default_reply
import os

LINE_NOTIFY_ACCESS_TOKEN = os.environ["LINE_NOTIFY_ACCESS_TOKEN"]

@respond_to('(.*)')
def mention_func(message,something):
    name = "[" + message.channel._client.users[message._body['user']]['real_name'] + " @ slack]\n"
    p = "curl -X POST https://notify-api.line.me/api/notify -H \'Authorization: Bearer ${LINE_NOTIFY_ACCESS_TOKEN}\' -F \'message={0}{1}\'".format(name,message.body['text'])
    req = os.system(p)

```

```
message.channel._client.users[message._body['user']]['real_name']
```
↑で投稿者のユーザ名を取得することができるので、グループトークのために使う。

```
@respond_to('(.*)')
```
↑はメンションされた全てのメッセージというワイルドカード。

Slackbotを起動するには
以下のコマンドを入力して、プログラムを起動する。

```$
$ python3 run.py
```

これで、SlackからLINEへ送信する機能が完成。

# LINEからSlackへ
次に、LINEからSlackへということを考えたい。
linebotsdkライブラリでLINEボットを作りたい。[^3]
https://developers.line.biz/en/

次にサーバ側の実装。

ディレクトリは以下。

```
├── LINE_to_Slack           #好きな名前で良い。
│   ├── Procfile            #デプロイに必要
│   ├── main.py             #本体
│   ├── requirements.txt　　 #デプロイに必要
│   └── runtime.txt　　　　　 #デプロイに必要
```

# 環境構築
ライブラリをインストールする。

```$:$
$ sudo pip3 install flask 
$ sudo pip3 install line-bot-sdk
```

```python:main.py
from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
import os
import slackweb
app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = os.environ["YOUR_CHANNEL_ACCESS_TOKEN"]
YOUR_CHANNEL_SECRET = os.environ["YOUR_CHANNEL_SECRET"]

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    webhooklink = ""
    slackinfo = slackweb.Slack(webhooklink)
    profile = line_bot_api.get_profile(event.source.user_id)
    MESSAGE = "[ " + profile.display_name + "からのメッセージ ]\n" + event.message.text
    slackinfo.notify(text=MESSAGE)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

```

ちなみに、送信元のLINEのユーザ名は以下のように取ることができる。↓

```
 profile = line_bot_api.get_profile(event.source.user_id)
 MESSAGE = "[ " + profile.display_name + "からのメッセージ ]\n" + event.message.text
```
これでmain.pyを実行すればlinebotが起動する。

```$:$
python3 main.py
```
これでLINEからSlackへの送信部は完成。
ここまでできたら双方でメッセージのやりとりができるようになっている。


# Herokuにデプロイする場合

herokuに登録
まだherokuに登録してない人は以下から登録する。
https://dashboard.heroku.com/

登録後、ターミナルからHerokuを扱うためheroku-cliをインストールし、ログインする。

```$:$
$ brew install heroku/brew/heroku
$ heroku login
```

Gitを使ってHerokuにデプロイ。

```$:$
$ cd path/to/your/linebot/directory
$ git init
$ git add . 
$ git commit -m "init"
$ heroku create [Your bot name] % http://[your bot name].herokuapp.com/
```

```$:$
$ git push heroku master
```

LINE messaging APIのChannel secret
Slackのbots API token等はHerokuの環境変数へ。
例↓

```$:$
$ heroku config:set YOUR_SECRET=hoge
$ heroku config:set YOUR_ACCESS_TOKEN=fuga
```

to_lineデプロイ時には以下が必要。[^4]

```
heroku ps:scale pbot=1
```

またto-line と to-slackはそれぞれ別々にデプロイする必要がある。

## License
Copyright (c) 2021 Kazuya yuda.
This software is released under the MIT License, see LICENSE.
https://opensource.org/licenses/mit-license.php

## Authors
kazuya yuda.

## References

「PythonのslackbotライブラリでSlackボットを作る」 https://qiita.com/sukesuke/items/1ac92251def87357fdf6  
「LINE Notify API Document」 https://notify-bot.line.me/doc/en/  
「FlaskでLINE botを実装し，herokuにdeployするまで」 https://qiita.com/suigin/items/0deb9451f45e351acf92  
「pythonで作ったSlackBotを常駐化するまでの備忘録」https://qiita.com/usomaru/items/6eed064690cdb7988e54  
