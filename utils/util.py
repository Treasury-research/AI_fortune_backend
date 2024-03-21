from urllib import parse
import logging
import requests
import re
import html
import json
from openai import OpenAI
client = OpenAI()
def stream_output(message=None, user_id=None,bazi_info=None):
    # Stream的格式：<chunk>xxxxx</chunk><chunk>{id:'xxxx'}</chunk>
    # streams = ["<chunk>", bazi_info, "</chunk>","<chunk>",f"{{'user_id':{user_id}}}","</chunk>"]
    # if message:
    #     yield f"{message}"
    if bazi_info:
        yield bazi_info.encode('utf-8')
        # answer = ""
    if user_id:
        user_data = {'user_id':user_id}
        json_user_data = json.dumps(user_data)
        yield f"<chunk>{json_user_data}</chunk>"


def get_coin_data(name):
    try:
        tidb_manager = TiDBManager()
        res = tidb_manager.select_coin_id(name = name)
        import requests
        base_url = 'https://pro-api.coinmarketcap.com'
        # Endpoint for getting cryptocurrency quotes
        endpoint = '/v2/cryptocurrency/quotes/latest'
        # Parameters
        params = {
            'id': str(res),  # Replace with the actual ID you want to query
        }

        # Headers
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': os.environ["CMC_API_KEY"],
        }

        # Make the request
        response = requests.get(base_url + endpoint, headers=headers, params=params)
        data = response.json()
        # print(data)
        coin_data = data['data'][str(res)]
        return coin_data
    except:
        return None


def get_messages(thread_id):
    import http.client
    import json
    conn = http.client.HTTPSConnection("api.openai.com")
    payload = ''
    headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'OpenAI-Beta': 'assistants=v1',
    'Authorization': 'Bearer '+os.environ["OPENAI_API_KEY"]
    }
    conn.request("GET", "/v1/threads/"+thread_id+"/messages", payload, headers)
    res = conn.getresponse()
    data = res.read()
    result = json.loads(data)
    return result

def cancel_run(thread_id,run_id):
    import http.client

    conn = http.client.HTTPSConnection("api.openai.com")
    payload = ''
    headers = {
    'User-Agent': 'Apifox/1.0.0 (https://apifox.com)',
    'OpenAI-Beta': 'assistants=v1',
    'Authorization': 'Bearer '+os.environ["OPENAI_API_KEY"]
    }
    conn.request("POST", "/v1/threads/"+thread_id+"/runs/"+run_id+"/cancel", payload, headers)
    res = conn.getresponse()
    data = res.read()
    logging.info(f"cancel run:{data.decode('utf-8')}")

def translate(text):
    GOOGLE_TRANSLATE_URL = 'http://translate.google.com/m?q=%s&tl=%s&sl=%s'
    text = parse.quote(text)
    url = GOOGLE_TRANSLATE_URL % (text,"en","zh-CN")
    response = requests.get(url)
    data = response.text
    expr = r'(?s)class="(?:t0|result-container)">(.*?)<'
    result = re.findall(expr, data)
    if (len(result) == 0):
        res = None
    else:
        res = html.unescape(result[0])
    return res

