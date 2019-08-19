# -*- coding: utf-8 -*-
from slackbot.bot import respond_to
from slackbot.bot import listen_to
from slackbot.bot import default_reply
import os

@respond_to('(.*)')
def mention_func(message,something):
    name = "[" + message.channel._client.users[message._body['user']]['real_name'] + " @ slack]\n"
    p = "curl -X POST https://notify-api.line.me/api/notify -H \'Authorization: Bearer \' -F \'message={0}{1}\'".format(name,message.body['text'])
    req = os.system(p)
