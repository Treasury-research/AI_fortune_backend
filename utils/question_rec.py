from openai import OpenAI
import json
import random
client = OpenAI()
def rec_question(bazi_info_gpt,user_message,lang):
    if lang=="En":
        system_prompt = f""""
    You are a master at asking questions. Below are some background knowledge and sample questions on the Eight Characteristics, which require you to generate three more Eight Character Numerology questions related to the background knowledge and sample questions.
    Background knowledge:
    {bazi_info_gpt}

    Sample question.
    {user_message}    
    """
        user_prompt = f"""Give me three relevant questions, note that the subject is the same as the subject of the question, and also give me questions that don't include my love life or significant other. Return as json, e.g. {{"response": list of three related questions}}"""
    else:
        system_prompt = f"""
        你是提问题的高手，下面是一些八字的背景知识和问题示例,需要你再生成和背景知识及问题示例相关的三个八字命理问题，注意是相关不是重复。
        背景知识：
        {bazi_info_gpt}

        问题示例:
        {user_message}    
        """
        user_prompt = f"""请你返回三个相关问题，注意主语与问题的主语一定要一致。以json的形式返回, 如{{"response":三个相关问题的list}}"""
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo-1106",                                          # 模型选择GPT 3.5 Turbo
        messages=[{"role": "system", "content": system_prompt},
                {"role": "user", "content":user_prompt}],
        max_tokens = 1024,
        temperature = 0,
        response_format={"type": "json_object"}

    )
    string_res = completion.choices[0].message.content.strip()
    string_res = json.loads(string_res)
    return string_res["response"]