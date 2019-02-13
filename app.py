import json
import os
from datetime import datetime
from pprint import pprint

import jwt
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request

app = Flask(__name__)

API_KEY = os.getenv('API_KEY')
SERVER_CONSUMER_KEY = os.getenv('SERVER_CONSUMER_KEY')
SERVER_ID = os.getenv('SERVER_ID')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
BOT_NO = os.getenv('BOT_NO')


def get_token(server_id, private_key):
    '''
    JWT から server token の生成
    '''
    # claim_set 生成時間及び 終了時間 (60分設定)
    crnt_time = int(datetime.now().strftime('%s'))
    exp_time = crnt_time + 3600

    claim_set = {
        'iss': server_id,
        'iat': crnt_time,
        'exp': exp_time
    }

    key = open(private_key).read()

    lw_jwt = jwt.encode(claim_set, key, algorithm='RS256')

    url = 'https://authapi.worksmobile.com/b/' + API_KEY + '/server/token'
    header = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'charset': 'utf-8'
    }
    payload = {
        'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer',
        'assertion': lw_jwt.decode('utf-8'),
    }
    r = requests.post(url, headers=header, params=payload)
    r.raise_for_status()
    return r.json().get('access_token', None)


@app.route('/', methods=['GET'])
def helthcheck():
    return 'Hello World'


@app.route('/callback', endpoint='callback', methods=['POST'])
def callback():
    data = request.get_json()
    # TODO　data['content']['text']がないケースもある模様　要確認
    text = data['content']['text']

    pprint(request)
    pprint(data)
    # TODO 暫定実装　（リクエスト毎に取得するのではなくバッチで定時取得する）
    access_token = get_token(SERVER_ID, PRIVATE_KEY)

    url = 'https://apis.worksmobile.com/' + API_KEY + '/message/sendMessage/v2'
    header = {
        'consumerKey': SERVER_CONSUMER_KEY,
        'Authorization': 'Bearer ' + access_token,
        'Content-Type': 'application/json'
    }
    if 'リスト' in text:
        content = {
            'type': 'listTemplate',
            'coverData': {
                'title': 'ん' * 1000,
                'subtitle': 'ん' * 1000,
                'backgroundImage': 'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_92x30dp.png'
            },
            'elements': [
                {
                    'title': 'あ' * 1000,
                    'subtitle': 'あ' * 1000,
                    'button': {
                        'text': 'ボタンのテキストその1 (googleへ)(googleへ)(googleへ)',
                        'link': 'http://google.com',
                    },
                },
                {
                    'title': 'https://amazon.com',
                    'subtitle': 'https://amazon.com',
                    'button': {
                        'text': 'ボタンのテキストその2 (amazonへ)(amazonへ)(amazonへ)',
                        'link': 'http://amazon.com',
                    },
                },
                {
                    'title': 'タイトルその3',
                    'subtitle': 'サブタイトルその3 (postback 1)(postback 1)(postback 1)',
                    'button': {
                        'text': 'ボタンのテキストその3 (postback 1)(postback 1)(postback 1)',
                        'postback': 'Postback No.1',
                    },
                },
                {
                    'title': 'タイトルその4',
                    'subtitle': 'サブタイトルその4 (postback 2)(postback 2)(postback 2)',
                    'button': {
                        'text': 'ボタンのテキストその4 (postback 2)(postback 2)(postback 2)',
                        'link': 'Postback No.2',
                    },
                },
            ],
            # 縦×横の2次元配列にする
            'buttons': [
                [
                    {
                        'text': 'その1 (googleへ)',
                        'link': 'http://google.com',
                    },
                    {
                        'text': 'その2 (amazonへ)',
                        'link': 'http://amazon.com',
                    },
                ],
                [
                    {
                        'text': 'その3 (postback 1)',
                        'postback': 'Postback No.1',
                    },
                    {
                        'text': 'その4 (postback 2)',
                        'link': 'Postback No.2',
                    },
                ],
            ]

        }
    elif 'ボタン' in text:
        buttons = []
        for i in range(10):
            buttons.append({
                'text': 'ボタンのテキストその{} 12345678901234567890123456789012345678901234567890'.format(i+1),
                'link': 'http://google.com',
            })
        content = {
            'type': 'buttonTemplate',
            'contentText': 'あ' * 1000,
            'buttons': buttons,
        }
    else:
        content = {
            'type': 'text',
            'text': 'ボットのオウム返し応答 => {}'.format(data['content']['text'])
        }

    payload = {
        'botNo': int(BOT_NO),
        'content': content
    }

    source = data['source']
    """
    ルームへの投稿
    {'content': {'text': '@fujitani_test グループ\u3000ボタン', 'type': 'text'},
    'createdTime': 1550052703843,
    'source': {'accountId': 'fu.10234@fujitani-test', 'roomId': '11689221'},
    'type': 'message'}

    DM投稿
    {'content': {'text': 'ボタン', 'type': 'text'},
    'createdTime': 1550052781912,
    'source': {'accountId': 'fu.10234@fujitani-test'},
    'type': 'message'}
    """
    if source.get('roomId'):
        payload.update({'roomId': source['roomId']})
    elif source.get('accountId'):
        payload.update({'accountId': source['accountId']})
    else:
        raise Exception('Invalid Request roomId or accountId required')

    r = requests.post(url, headers=header, data=json.dumps(payload))
    r.raise_for_status()
    pprint(r)
    pprint(r.json())
    return jsonify(r.json())


if __name__ == '__main__':
    load_dotenv('.env', override=True)
    app.run(debug=True)
