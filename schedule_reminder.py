import json
import pyttsx3
import time
import datetime as dt
from gen_input import gen_input as gen_touch_input
import os
def speak(text):
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[5].id)
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 0.6)
        time.sleep(0.5)
        engine.say(text)
        engine.runAndWait()
        del engine
def opening_apps(path):
    try:
        os.startfile(path)
    except FileNotFoundError:
        print(f"Error opening FileNotFoundError: {path}")

def reminder_excute(tasks_file='data/tasks.json'):
    current_time = dt.datetime.now().strftime('%H')
    day = dt.datetime.now().strftime('%a')

    with open(tasks_file, 'r') as f:
        tasks = json.load(f)

    for task in tasks:
        start_time = task['start']
        end_time = task['end']
        days = task.get('days', [])          # empty list = every day
        day_ok = (not days) or (day in days)

        if day_ok and start_time <= current_time < end_time:
            print('routine apps are starting confirmation needed')
            speak('routine apps are starting confirmation needed')
            conf = gen_touch_input()
            affirmative_responses = {
                'yes', 'y', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay',
                'confirm', 'confirmed', 'affirmative', 'go', 'go ahead',
                'do it', 'proceed', 'continue', 'correct', 'right', 'aye', 
                'start'
            }
            if conf in affirmative_responses:    
                print(task['message'])
                paths = task.get('paths', [])
                if paths:
                    print('paths exist')
                    print('starting applications...')
                    for p in paths:
                        print(p)
                        opening_apps(p)
                    print('everything sorted for you all aplications are opened')
                    speak('everything sorted for you all aplications are opened')
                    return
            else:
                return
            # print(task.get('paths', []))

def box_excute(name, tasks_file='data/tasks.json'):
    with open(tasks_file, 'r') as f:
        tasks = json.load(f)
    for task in tasks:
        if task['message'] == name:
            print('apps are starting confirmation needed')
            speak('apps are starting confirmation needed')
            conf = gen_touch_input()
            if conf.lower() in ['yes', 'y', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay']:
                paths = task.get('paths', [])
                if paths:
                    print('paths exist')
                    print('starting applications...')
                    for p in paths:
                        print(p)
                        opening_apps(p)
                    print('everything sorted for you all aplications are opened')
                    speak('everything sorted for you all aplications are opened')
                    return
        else:
            print('returning back to main')
            speak('returning back to main')

    print('nothing sheduled for now')
    speak('nothing sheduled for now')

box_excute('test')