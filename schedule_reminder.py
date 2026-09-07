import json
import pyttsx3
import datetime as dt
from gen_input import gen_input 
import os

def speak(text):
    print('starting speak function')
    engine = pyttsx3.init()
    engine.setProperty('rate', 185)
    engine.setProperty('volume', 0.6)
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
            conf = gen_input()
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
            else:
                continue
            # print(task.get('paths', []))
    print('nothing sheduled for now')
    speak('nothing sheduled for now')