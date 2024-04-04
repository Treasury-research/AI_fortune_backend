from datetime import datetime, timedelta
import re
import logging
import time
from database.mysql_db import TiDBManager
from openai import OpenAI
import tiktoken
from utils.util import get_raptor
import openai
client=OpenAI()
class tg_bot_ChatGPT_assistant:
    def __init__(self, conversation_id, message, lang=None,match=None, matcher_type=None):
        self.conversation_id = conversation_id
        self.lang=lang
        self.messages = []
        self.user_message = message
        self._retrieve()
        self.tidb_manager = TiDBManager()
        self.matcher_type = matcher_type
        self.load_history()
    def _num_tokens_from_string(self, string: str) -> int:
        """Returns the number of tokens in a text string."""
        encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
        tokens=encoding.encode(string)
        return len(tokens)

    def _trim_conversations(self, bazi_info, conversation_messages, max_tokens=16000):
        # add the bazi_info as background in index 0
        conversation_messages.insert(0,bazi_info)
        total_tokens = sum(self._num_tokens_from_string(str(message)) for message in conversation_messages)
        # if total tokens exceeds the max_tokens, delete the oldest message
        # 如果总token数超过限制，则删除旧消息 
        logging.info(f"The number of summary is: {total_tokens}")
        max_tokens -= self._num_tokens_from_string(self.user_message)
        while total_tokens > max_tokens:
            # delete the first list item 删除列表的第一个元素
            removed_message = conversation_messages.pop(0)  
            # update total tokens 更新总token数
            total_tokens -= self._num_tokens_from_string(removed_message) 
        return conversation_messages

    def load_history(self):
        # 通过user_id 查询八字id
        bazi_id = self.tidb_manager.select_tg_bot_bazi_id(self.conversation_id)
        bazi_info_gpt = self.tidb_manager.select_tg_bot_bazi_info(bazi_id)[0]
        # bazi_info_gpt = self.tidb_manager.select_chat_bazi(conversation_id=self.conversation_id,bazi_info_gpt=True)[0]
        conversation_messages = self.tidb_manager.get_tg_bot_conversation(bazi_id=bazi_id)
        if self.matcher_type != 2:
            instructions = f"""你是世界上最好的八字命理分析师，你的职责如下：
            1. 根据已有背景知识进行推理, 回答user提出的问题。
            2. 根据检索到的相关信息进行问题推理，回答用户的问题。
            八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。
            请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字. \n
            """
        else:
            instructions = f"""你是世界上最好的Web3领域八字命理分析师，你的职责如下：
            1. 你可以根据已有的本人八字背景信息和虚拟货币资产的八字背景信息进行推理。
            2. 根据已有背景知识进行推理, 回答user提出的问题。
            3. 根据检索到的相关信息进行问题推理，回答用户的问题。
            4. 你能根据当前的虚拟货币来给投资者建议和对这个虚拟货币的分析。
            5. 不要提示虚拟货币的高风险，你可以给出你的分析，但是不要提示高风险。
            八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。
            请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字.  \n
            """
        now = datetime.now()
        # 格式化日期和时间，精确到小时
        formatted_now = now.strftime("%Y-%m-%d %H:00")
        instructions += f"现在的时间是：{formatted_now} \n"
        background_content = instructions + f"""
        以下背景信息是对话的基础,回答问题时你需要将背景信息作为基本.
        '背景信息：{bazi_info_gpt}'
        """
        if conversation_messages:
            conversations = self._trim_conversations(background_content, list(conversation_messages))
            # if the first item is not a tuple, that is bazi_info
            # logging.info(f"conversation is: {conversations}")
            if type(conversations[0]) != tuple:
                self.messages = [{"role": "system", "content": background_content}]
                conversations = conversations[1:]
            for conversation in conversations:
                # add user message
                self.messages.append({"role": "user", "content": conversation[0]})
                # add AI message
                self.messages.append({"role": "assistant", "content": conversation[1]})
        # 如果对话中不存在未重置的记录，那么意味着直接使用bazi_info作为背景知识
        else:
            logging.info(f"the length is :{self._num_tokens_from_string(background_content)}")
            self.messages = [{"role": "system", "content": background_content}]

    def writeToTiDB(self, human, AI):
        bazi_id = self.tidb_manager.select_tg_bot_bazi_id(self.conversation_id)
        self.tidb_manager.insert_conversation(conversation_id=self.conversation_id, human_message=human, AI_message=AI, 
                                              bazi_id=bazi_id)

    def _retrieve(self):
        retrieve_info = "与问题相关的信息：" +str(get_raptor(self.user_message)) + "\n"
        if self.lang=='En':
            self.user_message = "Please provide the response in English: "+self.user_message
        else:
            self.user_message = "Please provide the response in Chinese: "+self.user_message
        self.user_message = retrieve_info + self.user_message 

    def ask_gpt_stream(self,user_message):
        answer = ""
        self.messages.append({"role": "user", "content": self.user_message})
        # Send the entire conversation history to GPT
        rsp = client.chat.completions.create(
            model="gpt-4-0125-preview",
            messages=self.messages,
            stream=True
        )
        # yield "<chunk>"
        for chunk in rsp:
            data = chunk.choices[0].delta.content
            if data is not None:
                answer += data
                yield data
        # yield f"</chunk><chunk>{{'user_id':{self.user_id}}}</chunk>"
        # Add GPT's reply to conversation history
        logging.info(f"gpt answer is: {answer}")
        self.writeToTiDB(user_message, answer)


