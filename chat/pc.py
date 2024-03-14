from datetime import datetime, timedelta
import re
import logging
import time
from database.mysql_db import TiDBManager
from openai import OpenAI
client = OpenAI()

class ChatGPT_assistant:
    def __init__(self, conversation_id, lang=None,match=None, matcher_type=None):
        self.conversation_id = conversation_id
        self.lang=lang
        self.assistant_id, self.thread_id, self.run_id= None,None,None
        self.tidb_manager = TiDBManager()
        self.match=match
        self.matcher_type = matcher_type
        self.load_history()
        logging.info(f"{self.conversation_id}, {self.assistant_id},{self.thread_id}")

    
    def load_history(self):
        file_ids = ["file-jHT2dMXPx90e8daOC9ZNNT5m"]
        assistant_id = "asst_BtScD1XxQ06cnnBrWN6IM9gt"
        res = self.tidb_manager.select_chat_bazi(conversation_id=self.conversation_id,assistant_id=True,thread_id=True)
        if res and res[0] is not None and res[1] is not None:
            logging.info(f"self.assistant_id, self.thread_id {res}")
            self.assistant_id, self.thread_id = res[0],res[1]
        else:
            # # 获取当前日期和时间
            # now = datetime.now()
            # # 格式化日期和时间，精确到小时
            # formatted_now = now.strftime("%Y-%m-%d %H:00")
            # assistant = client.beta.assistants.create(
            #     name="bazi",
            #     instructions=f"""你是世界上最好的八字命理分析师，根据已有背景知识进行推理, 回答user提出的问题。
            #     根据检索到的相关信息进行问题推理，回答用户的问题。
            #     八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。
            #     请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字. 
            #     不要出现'克夫克妻'等字眼。不需要给出参考资料来源。\n
            #     """,
            #     model="gpt-4-0125-preview",
            #     tools=[{"type": "retrieval"}],
            #     file_ids=file_ids
            # )
            self.assistant_id = assistant_id
            thread = client.beta.threads.create()
            self.thread_id = thread.id
            self.tidb_manager.update_chat(conversation_id=self.conversation_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
            bazi_info_gpt = self.tidb_manager.select_chat_bazi(conversation_id=self.conversation_id, bazi_info_gpt=True)
            prompt = f"""
                以下背景信息是对话的基础,回答问题时你需要将背景信息作为基本.
                '背景信息：{bazi_info_gpt}'
                    """
            message = client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content= prompt,
            )

    def reset_conversation(self):
        self.thread_id = None
        self.tidb_manager.update_reset_delete(conversation_id=self.conversation_id, reset=True)
        return True

    def ask_gpt_stream(self, user_message):
        logging.info(f"开始聊天")
        now = datetime.now()
        # 格式化日期和时间，精确到小时
        formatted_now = now.strftime("%Y-%m-%d %H:00")
        if self.lang=='En':
            user_message = f"Time now is {formatted_now}. Please provide the response in English: "+user_message
        else:
            user_message = f"Time now is {formatted_now}. Please provide the response in Chinese: "+user_message
        message = client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content= user_message,
        )

        run = client.beta.threads.runs.create( 
            thread_id=self.thread_id,
            assistant_id=self.assistant_id)
        self.wait_on_run(run,user_message)
        logging.info(f"")
        messages = client.beta.threads.messages.list(thread_id=self.thread_id)
        res = messages.data[0].content[0].text.value
        res = self.remove_brackets_content(res)
        logging.info(f"final res:{res}")
        yield res

    def remove_brackets_content(self,sentence):
        import re
        # 使用正则表达式匹配"【】"及其内部的内容，并将其替换为空
        new_sentence = re.sub(r'【.*?】', '', sentence)
        return new_sentence
    
    def wait_on_run(self, run,message=None):
        logging.info(f"{message}")
        while run.status == "queued" or run.status == "in_progress":
        #     try:
        #         logging.info("222")
        #         messages = client.beta.threads.messages.list(thread_id=self.thread_id)
        #         # if len(messages['data'][0]['content'])>0:
        #         logging.info("333")
        #         if len(messages.data[0].content)>0:
        #             logging.info("444")
        #             res = messages.data[0].content[0].text.value
        #             logging.info("555")
        #             logging.info(f"now the message is :{res}")
        #             if res != message:
        #                 logging.info("666")
        #                 logging.info(f"exit early")
        #                 break
        #     except:
        #         logging.info("777")
            run = client.beta.threads.runs.retrieve(
                thread_id=self.thread_id,
                run_id=run.id,
            )
            time.sleep(2)
        # return run
        logging.info(run.status)
