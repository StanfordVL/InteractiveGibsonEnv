from openai import OpenAI
import os
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)  # for exponential backoff

client = OpenAI(
    # This is the default and can be omitted
    api_key=os.environ.get("OPENAI_API_KEY"),
)
@retry(wait=wait_random_exponential(min=0.1, max=1), stop=stop_after_attempt(6))
def call_gpt_with_retry(prompt, sys_content="You are an AI assistant that speaks English.",
    model="gpt-3.5-turbo",history=None,temperature=0,**kwargs):

    messages=[
        {
            "role": "system",
            "content": sys_content
        },
    ]

    if history is not None:
        for message in history:
            messages.append(message)

    messages.append({
                "role": "user",
                "content": prompt
            })
    
    return client.chat.completions.create(model=model,
        messages=messages,temperature=temperature,
        **kwargs).choices[0].message.content.strip()