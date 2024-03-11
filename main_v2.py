import openai
import sxtwl
import json
import os
import time
import html
from urllib import parse
import re
from flask import Flask, Response, request, stream_with_context, jsonify
from flask_cors import CORS
import os
import requests
import random
import openai
from openai import OpenAI
import mysql.connector
from dbutils.pooled_db import PooledDB
from urllib.parse import urlparse
from datetime import datetime, timedelta
import uuid
import pymysql
import tiktoken
import logging
from bazi import baziAnalysis
from al import baziMatch
from lunar_python import Lunar, Solar
from bazi_gpt import bazipaipan
from bp_router.tg import tg_bot
from bp_router.pc import pc
# 假设你的DATABASE_URL如下所示：
# 配置日志记录
logging.basicConfig(filename='AI_fortune.log', level=logging.INFO, encoding='utf-8',
                    format='%(asctime)s - %(levelname)s - %(message)s')
app = Flask(__name__)
# 跨域支持
CORS(app, resources=r'/*')
# 注册蓝图，并指定其对应的前缀（url_prefix）
app.register_blueprint(tg_bot, url_prefix="/api/tg_bot")
app.register_blueprint(pc, url_prefix="/api")



@app.route('/test')
def test():
    return jsonify({"res":"test!"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
