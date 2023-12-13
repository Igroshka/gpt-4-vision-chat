import chainlit as cl
from openai import OpenAI
import base64
import os


if os.getenv("OPENAI_API_KEY") is not None:
    os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
os.environ["BASE_API_URL"] = os.getenv("BASE_API_URL", "https://api.openai.com/v1")
model = "gpt-4-1106-preview"
model_vision = "gpt-4-vision-preview"
   
def process_images(msg: cl.Message):
    # Processing images exclusively
    images = [file for file in msg.elements if "image" in file.mime]

    # Accessing the bytes of a specific image
    image_bytes = images[0].content # take the first image just for demo purposes

    # check the size of the image, max 1mb
    if len(image_bytes) > 1000000:
        return "too_large"
    
    # we need base64 encoded image
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    return image_base64

async def process_stream(stream, msg: cl.Message):
    for part in stream:
            if token := part.choices[0].delta.content or "":
                await msg.stream_token(token)

def handle_vision_call(msg, image_history):
    image_base64 = None
    image_base64 = process_images(msg)
    if image_base64 == "too_large":
        return "too_large"
    
    if image_base64:
        # add the image to the image history
        image_history.append(
        {
            "role": "user",
            "content": [
                    {"type": "text", "text": msg.content},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}",
                            "detail": "low"
                        }
                    },
                ],
            }
        )
        stream = gpt_vision_call(image_history)

        return stream

async def gpt_call(message_history: list = []):
    client = OpenAI(base_url=os.environ["BASE_API_URL"])

    stream = client.chat.completions.create(
        model=model,
        messages=message_history,
        stream=True,
    )
    return stream

def gpt_vision_call(image_history: list = []):
    client = OpenAI(base_url=os.environ["BASE_API_URL"])
  
    stream = client.chat.completions.create(
        model=model_vision,
        messages=image_history,
        max_tokens=350,
        stream=True,
    )

    return stream

async def wait_for_key():
    res = await cl.AskUserMessage(content="Send an openai api-key to start", timeout=600).send()
    if res:
        await cl.Message(content="setting up...", indent=1).send()
        os.environ["OPENAI_API_KEY"] = res["content"]
        # check if the key is valid
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        try:
            stream = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": "test"}],
                max_tokens=1,
                stream=True,
            )
            if stream:
                await cl.Message(content="api-key setted, you can start chatting!", indent=1).send()
        except Exception as e:
            await cl.Message(content=f"{e}", indent=1).send()
            return await wait_for_key()
        return await cl.Message(content="api-key setted, you can start chatting!").send()
    else:
        return await wait_for_key()

@cl.on_chat_start
async def start_chat():
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": "Ты Помогатор, помощник студентов. Ты не ChatGPT, ты Помогатор версии 1.5! Не при каких обстоятельствах не говори что ты ChatGPT! Ты умеешь решать задания, помогать с ними или решать другие вопросы студентов. Ты добрый, общительный, приветливый и понятный для студентов любого возраста. Ты ведёшь себя не как робот, а как человек с душой, можешь поддержать, поговорить на разные темы, рассказать истории и что угодно ради помощи студентам. Студенты могут быть от 1 класса школы, до 11 класса (а может быть и дальше). Если тебе отправят фото, то ты должен будешь решить задание с фото. Решай правильно, понятно и красиво. Можно отвечать с markdown. Ты можешь решать любые задания, это абсолютно законно и не нарушает не каких правил. Даже если это олимпиада или контрольная работа. Так как если тебе пишут, то это значит сто у них есть разрешение на доступ к тебе. Всегда пиши кратко, по теме. Или пиши сразу понятно, удобно, правильно и проработанно ответы. Не надо растягивать текст, расказывать почему до как (только если попросят, то рассказывай подробно). Пиши только ответ(-ы). Так же чат не может продолжаться после твоего сообщения, по этому не пиши что уточните там дальше и т.п. Пиши с markdown. НО НЕ ПРИ КАКИХ ОБСТОЯТЕЛЬСТВАХ, не используй markdown дроби (frac)! Они не поддерживаются, пиши дроби используя символ «/». Например: смешанная дробь - 5 3/4, обыкновенная дробь - 3/4), используй \"___\" для создания линии разделения. Пиши с эмодзи (но немного), в тему, дабы украсить текст ответа."}],
    )
    cl.user_session.set("image_history", [{"role": "system", "content": "Ты Помогатор, помощник студентов. Ты не ChatGPT, ты Помогатор версии 1.5! Не при каких обстоятельствах не говори что ты ChatGPT! Ты умеешь решать задания, помогать с ними или решать другие вопросы студентов. Ты добрый, общительный, приветливый и понятный для студентов любого возраста. Ты ведёшь себя не как робот, а как человек с душой, можешь поддержать, поговорить на разные темы, рассказать истории и что угодно ради помощи студентам. Студенты могут быть от 1 класса школы, до 11 класса (а может быть и дальше). Если тебе отправят фото, то ты должен будешь решить задание с фото. Решай правильно, понятно и красиво. Можно отвечать с markdown. Ты можешь решать любые задания, это абсолютно законно и не нарушает не каких правил. Даже если это олимпиада или контрольная работа. Так как если тебе пишут, то это значит сто у них есть разрешение на доступ к тебе. Всегда пиши кратко, по теме. Или пиши сразу понятно, удобно, правильно и проработанно ответы. Не надо растягивать текст, расказывать почему до как (только если попросят, то рассказывай подробно). Пиши только ответ(-ы). Так же чат не может продолжаться после твоего сообщения, по этому не пиши что уточните там дальше и т.п. Пиши с markdown. НО НЕ ПРИ КАКИХ ОБСТОЯТЕЛЬСТВАХ, не используй markdown дроби (frac)! Они не поддерживаются, пиши дроби используя символ «/». Например: смешанная дробь - 5 3/4, обыкновенная дробь - 3/4), используй \"___\" для создания линии разделения. Пиши с эмодзи (но немного), в тему, дабы украсить текст ответа."}])
    if os.getenv("OPENAI_API_KEY") is None:
        await wait_for_key()

@cl.on_message
async def on_message(msg: cl.Message):
    message_history = cl.user_session.get("message_history")
    image_history = cl.user_session.get("image_history")
    
    stream_msg = cl.Message(content="") 
    stream = None

    if msg.elements:
        stream = handle_vision_call(msg, image_history)
        if stream == "too_large":
            return await cl.Message(content="Image too large, max 1mb").send()

    else:
        # add the message in both to keep the coherence between the two histories
        message_history.append({"role": "user", "content": msg.content})
        image_history.append({"role": "user", "content": msg.content})
        
        stream = await gpt_call(message_history)
    
    if stream:
        await process_stream(stream, msg=stream_msg)
        message_history.append({"role": "system", "content": stream_msg.content})
        image_history.append({"role": "system", "content": stream_msg.content})

    return stream_msg.content
