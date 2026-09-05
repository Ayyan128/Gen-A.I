import os
import json
import random
from datetime import datetime as dt
from groq import Groq
from gen_speak import gen_voice_package  as vpack

def gen_greet_fallback(time):
    print('entered fallback greet')
    try:
        with open("data/greetings.json") as f:
            greeting = json.load(f)
        return random.choice(greeting[time])
    except Exception:
        return f"Good {time}"


def gen_greet_api(period):
    with open("data/API_KEY.txt") as f:
        gen_api = f.read().strip()
    try:
        client = Groq(api_key=gen_api)

        chat = client.chat.completions.create(
            model = 'openai/gpt-oss-120b',
            max_tokens=300,
            reasoning_effort='low', 
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Write one short greeting (5-10 words) that a formal, "
                        f"witty British AI assistant like JARVIS would say to its "
                        f"user in the {period}. No quotes, no punctuation at the "
                        f"end, just the greeting text itself, nothing else."
                    ),
                }
            ],
        )

        return chat.choices[0].message.content.strip()

    except Exception:
        gen_greet_fallback(period)

def gen_greet():
    now = dt.now()
    current_hour = now.hour
    current_time = now.strftime("%I:%M %p")
    day = now.strftime("%A")
    date = now.strftime("%B %d, %Y")

    if current_hour < 12:
        period = "morning"
    elif current_hour < 17:
        period = "afternoon"
    elif current_hour < 21:
        period = "evening"
    else:
        period = "night"

    message = gen_greet_api(period)
    if not message:
        message = f"Good {period}"

    if period == "morning":
        full_message = (
            f"{message} Sir. Today is {day}, {date}. "
            f"It is currently {current_time}."
        )
    else:
        full_message = (
            f"{message} Sir. "
            f"It is currently {current_time}."
        )

    vpack.gen_jarvis_eng(full_message)
