print('loading packages...')
from gen_greet import gen_greet
import sys
import os
from groq import Groq
from gen_function_excute import excute_tool
from gen_speak import gen_voice_package as vpkg
from schedule_reminder import reminder_excute
import getpass

# ---- Configuration ----
print('Intializing Gen A.I....')
MODEL = "openai/gpt-oss-120b"    
MAX_TOKENS = 1024                    # max tokens per response
EFFORTS = 'low'
CODE = 'JOgyd5jug'
SYSTEM_PROMPT = (
    "You are a helpful, friendly assistant like Jarvis. "
    "You can chat normally, but you also control real device tools "
    "(opening websites, checking RAM/CPU usage, running system analysis, "
    "shutting down, or restarting the machine). "
    f"If, and only if, the user's message is clearly asking you to do one of "
    f"those tool actions, reply with EXACTLY the single token {CODE} and "
    "nothing else — no punctuation, no explanation. For every other message, "
    "just respond normally as a conversational assistant."
)

# --------------------------------
# Assitent Function
# ----------------------------------

def gen_routine_excution():
    vpkg.gen_jarvis_eng('starting the routine apps confirmation needed')
    conf = input().strip().lower()
    affirmative_responses = {
        'yes', 'y', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay',
        'confirm', 'confirmed', 'affirmative', 'go', 'go ahead',
        'do it', 'proceed', 'continue', 'correct', 'right', 'aye', 
        'start'
    }
    if conf in affirmative_responses:
        excute_tool()
    else:
        exit()

def main():
    with open("data/API_KEY") as f:
        api_key = f.read().strip()
        print('api_key done')
    if not api_key:
        print("ERROR: Please set the GROQ_API_KEY environment variable.")
        sys.exit(1)

    client = Groq(api_key=api_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    print('system prompt done')

    print("All Done")
    

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # temperpory exit system

        if user_input.lower() in ("exit", "bye", "packup"):
            exit_code = getpass.getpass(prompt='Exit Code : ', echo_char='*')
            if exit_code == '12':
                print("Goodbye!")
                break
            else:
                continue

        if user_input.lower() == "reset":
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            print("(conversation history cleared)\n")
            continue

        # Add user message to history
        messages.append({"role": "user", "content": user_input})

        try:
            response = client.chat.completions.create(
                model=MODEL,
                max_tokens=MAX_TOKENS,
                messages=messages,
                reasoning_effort=EFFORTS
            )
        except Exception as e:
            print(f"\n[Error contacting API: {e}]\n may be api ket expired or invalid, please check your API key in data/API_KEY file\n")
            messages.pop()  # remove the failed user message so history stays clean
            continue

        reply_text = (response.choices[0].message.content or "").strip()

        if reply_text == CODE:
            print('excuting tool...')
            # Model decided this is a tool request — hand it off and
            # get a real result back instead of running it silently.
            result = excute_tool(user_input)
            if result is not None:
                print(f"AI: {result}\n")
                assistant_msg = str(result)
            else:
                assistant_msg = "I attempted a tool action but it failed."

            # Keep history clean: store what actually happened, not the
            # raw trigger code, so future turns have real context.
            messages.append({"role": "assistant", "content": assistant_msg})
            continue

        print(f"AI: {reply_text}\n")
        vpkg.gen_jarvis_eng(reply_text)
        # Add assistant reply to history so context is preserved
        messages.append({"role": "assistant", "content": reply_text})


if __name__ == "__main__":
    gen_greet()
    gen_routine_excution()
    main()