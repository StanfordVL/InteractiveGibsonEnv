import openai
import time


def get_gpt_output(message, model="gpt-3.5-turbo", max_tokens=512, temperature=0):
    messages = [
        {"role": "system", "content": "You are a friendly assistant. Your answers are JSON only."},
        {"role": "assistant", "content": "{\"message\": \"Understood. I will output my answers in JSON format.\" }" },
        {"role": "user", "content": message}
        ] 
    kwargs = {"response_format": { "type": "json_object" }}
    try:
        chat = openai.OpenAI().chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            **kwargs
            )
    except Exception as e:
        print(f'{e}\nTry after 1 min')
        time.sleep(61)
        chat = openai.OpenAI().chat.completions.create(
            messages=messages,
            model=model,
            temperature=temperature,
            **kwargs
            )
    reply = chat.choices[0].message.content 
    return reply