import pyttsx3

class gen_voice_package:

    def gen_jarvis_eng(text):
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[5].id)
        engine.setProperty("rate", 170)
        engine.setProperty("volume", 0.6)
        engine.say(text)
        engine.runAndWait()
        del engine

    # BackUp Voice
    def gen_friday_eng(text):
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[6].id)
        engine.setProperty("rate", 190)
        engine.setProperty("volume", 0.7)
        engine.say(text)
        engine.runAndWait()
        del engine

    def gen_kal_hindi(text):
        engine = pyttsx3.init()
        voices = engine.getProperty("voices")
        engine.setProperty("voice", voices[3].id)
        engine.setProperty("rate", 190)
        engine.setProperty("volume", 0.7)
        engine.say(text)
        engine.runAndWait()
        del engine


