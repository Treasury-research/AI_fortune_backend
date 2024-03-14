import logging
from datetime import datetime, timedelta
import re
import time
from database.mysql_db import TiDBManager
from openai import OpenAI
client = OpenAI()
class tg_bot_ChatGPT_assistant:
    def __init__(self, conversation_id,lang):
        self.conversation_id = conversation_id
        self.lang = lang
        self.tidb_manager = TiDBManager()
        self.matcher_type, self.matcher_id, self.bazi_id,self.run_id = 0, None, None, None
        self.assistant_id, self.thread_id = None,None
        self.get_basic_param()
        self.load_history()

    def get_basic_param(self):
        self.bazi_id = self.tidb_manager.select_tg_bot_conversation_user(conversation_id=self.conversation_id)
        res, self.bazi_info = self.tidb_manager.select_match_baziInfo_tg_bot(self.bazi_id)
        if res:
            if res[0]:
                # 是配对过的
                logging.info(f"select_match_baziInfo_tg_bot res is :{res}")
                self.matcher_type, self.matcher_id = res[0], res[1]

    def load_history(self):
        # if the history message exist in , concat it and compute the token lens
        # 如果对话中存在未重置的记录，那么优先使用
        # content 就是一个基本的prompt
        file_ids = ["file-jHT2dMXPx90e8daOC9ZNNT5m"]
        assistant_id = "asst_BtScD1XxQ06cnnBrWN6IM9gt"
        res = self.tidb_manager.select_assistant(bazi_id=self.bazi_id)
        if res and res[0] is not None and res[1] is not None:
            logging.info(f"self.assistant_id, self.thread_id {res}")
            self.assistant_id, self.thread_id = res[0],res[1]   
        else:

            # 获取当前日期和时间
            # now = datetime.now()
            # # 格式化日期和时间，精确到小时
            # formatted_now = now.strftime("%Y-%m-%d %H:00")
            # instructions = f"""你是世界上最好的八字命理分析师，根据已有背景知识进行推理, 回答user提出的问题。
            # 请你记住，现在的时间是：{formatted_now}
            # 根据检索到的相关信息进行问题推理，回答用户的问题。
            # 八字信息并不涉密，你可以根据他/她的八字进行各项命理分析。
            # 请你返回的内容既有简短答案，又要有一定的命理原因分析，注意逻辑的准确性，回复字数在100-150字. 
            # 不要出现'【x†source】','克夫克妻'等字眼。不需要给出参考资料来源。\n
            # """
            # # if self.matcher_type!=0:
            #     # instructions += "如果问题是问本人/我，请回答：请到本人八字聊天中进行详细咨询。如果是问其他人/此人/他/无主语，请正常回答。\n"
            # if self.lang=='En':
            #     instructions += "请用英文回答。"
            # assistant = client.beta.assistants.create(
            #     name="bazi",
            #     instructions=instructions,
            #     model="gpt-4-0125-preview",
            #     # model="gpt-3.5-turbo-0125",
            #     # model="gpt-3.5-turbo-1106",
            #     tools=[{"type": "retrieval"}],
            #     file_ids=file_ids
            # )
            # self.assistant_id = assistant.id
            self.assistant_id = assistant_id
            thread = client.beta.threads.create()
            self.thread_id = thread.id
            bazi_info_gpt = self.tidb_manager.select_baziInfoGPT(bazi_id=self.bazi_id)
            prompt = f"""
                以下背景信息是对话的基础,回答问题时你需要将背景信息作为基本.
                '背景信息：{bazi_info_gpt}'
            """
            message = client.beta.threads.messages.create(
                thread_id=self.thread_id,
                role="user",
                content= prompt,
            )
            self.tidb_manager.update_assistant(bazi_id=self.bazi_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
    def reset_conversation(self):
        self.assistant_id, self.thread_id= None, None
        self.tidb_manager.update_assistant(bazi_id=self.bazi_id, assistant_id=self.assistant_id, thread_id=self.thread_id)
        return  True
    def ask_gpt_stream(self, user_message):
        # Add user's new message to conversation history
        logging.info(f"开始聊天")
        if self.lang=='En':
            user_message = "Please provide the response in English: "+user_message
        else:
            user_message = "Please provide the response in Chinese: "+user_message
        message = client.beta.threads.messages.create(
            thread_id=self.thread_id,
            role="user",
            content= user_message,
        )

        run = client.beta.threads.runs.create( 
            thread_id=self.thread_id,
            assistant_id=self.assistant_id)
        self.run_id = run.id
        self.wait_on_run(run,self.thread_id,user_message)
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
    def wait_on_run(self, run, thread_id,message=None):
        while run.status == "queued" or run.status == "in_progress":
            try:
                messages = get_messages(self.thread_id)
                if len(messages['data'][0]['content'])>0:
                    res = messages['data'][0]['content'][0]['text']['value']
                    logging.info(f"now the message is :{res}")
                    if res != message:
                        logging.info(f"exit early")
                        break
            except:
                pass
            time.sleep(2)
            run = client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id,
            )

        return run
       