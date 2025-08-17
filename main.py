import datetime
import json
import os
import queue
import random
import struct
import subprocess
import sys
import time
import threading
import re
import webbrowser

import google.generativeai as genai
import pvporcupine
import vosk
import yaml
from fuzzywuzzy import fuzz
from pvrecorder import PvRecorder
from rich import print
import pygame
import osascript
import requests

import config

# Try to import TTS module with fallback
try:
    import tts
except Exception as e:
    print(f"Warning: Could not import advanced TTS module: {e}")
    print("Falling back to simple TTS...")
    try:
        import tts_simple as tts
    except:
        class SimpleTTS:
            @staticmethod
            def va_speak(text):
                subprocess.run(['say', text])
        tts = SimpleTTS()

# Import smart features
try:
    from smart_features import smart_features
    print("🧠 Smart features loaded successfully!")
except ImportError:
    print("⚠️  Smart features not available")
    smart_features = None

# Constants
CDIR = os.getcwd()
VA_CMD_LIST = yaml.safe_load(
    open('commands.yaml', 'rt', encoding='utf8'),
)

# ChatGPT vars
system_message = {"role": "system", "content": "Ты голосовой ассистент из железного человека по имени Джарвис. Отвечай кратко, по-дружески и с легким техническим юмором."}
message_log = [system_message]

# Initialize pygame mixer
pygame.mixer.init()

# PORCUPINE
porcupine = pvporcupine.create(
    access_key=config.PICOVOICE_TOKEN,
    keywords=['jarvis'],
    sensitivities=[1]
)

genai.configure(api_key=config.GEMINI_API_KEY)

# VOSK
model = vosk.Model("model_small")
samplerate = 16000
device = config.MICROPHONE_INDEX
kaldi_rec = vosk.KaldiRecognizer(model, samplerate)
q = queue.Queue()

def gpt_answer():
    global message_log
    try:
        user_input = "\n".join([m["content"] for m in message_log if m["role"] == "user"])
        system_prompt = next((m["content"] for m in message_log if m["role"] == "system"), "")

        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(f"{system_prompt}\n\nПользователь: {user_input}")
        return response.text

    except Exception as ex:
        return f"Извините, возникла проблема с подключением к AI: {ex}"

def play(phrase, wait_done=True):
    global recorder
    filename = f"{CDIR}/sound/"

    phrase_map = {
        "greet": f"greet{random.choice([1, 2, 3])}.wav",
        "ok": f"ok{random.choice([1, 2, 3])}.wav",
        "not_found": "not_found.wav",
        "thanks": "thanks.wav",
        "run": "run.wav",
        "stupid": "stupid.wav",
        "ready": "ready.wav",
        "off": "off.wav",
        "error": "error.wav",
        "working": "working.wav"
    }

    filename += phrase_map.get(phrase, "ok1.wav")

    if wait_done:
        recorder.stop()

    try:
        if os.path.exists(filename):
            sound = pygame.mixer.Sound(filename)
            sound.play()
            
            if wait_done:
                while pygame.mixer.get_busy():
                    time.sleep(0.1)
        else:
            print(f"Sound file not found: {filename}")
    except pygame.error as e:
        print(f"Error playing sound {filename}: {e}")
    finally:
        if wait_done:
            recorder.start()

def va_respond(voice: str):
    global recorder, message_log
    print(f"🎤 Распознано: {voice}")

    cmd = recognize_cmd(filter_cmd(voice))
    print(f"📋 Команда: {cmd}")

    if len(cmd['cmd'].strip()) <= 0:
        return False
    elif cmd['percent'] < 70 or cmd['cmd'] not in VA_CMD_LIST.keys():
        # Check for AI conversation triggers
        ai_triggers = ["скажи", "расскажи", "что такое", "как дела", "привет"]
        if any(trigger in voice.lower() for trigger in ai_triggers):
            message_log.append({"role": "user", "content": voice})
            response = gpt_answer()
            message_log.append({"role": "assistant", "content": response})

            recorder.stop()
            tts.va_speak(response)
            time.sleep(0.5)
            recorder.start()
            return False
        else:
            play("not_found")
            tts.va_speak("Команда не распознана")
            time.sleep(1)
        return False
    else:
        execute_cmd(cmd['cmd'], voice)
        return True

def filter_cmd(raw_voice: str):
    cmd = raw_voice

    for x in config.VA_ALIAS:
        cmd = cmd.replace(x, "").strip()

    for x in config.VA_TBR:
        cmd = cmd.replace(x, "").strip()

    return cmd

def recognize_cmd(cmd: str):
    rc = {'cmd': '', 'percent': 0}
    for c, v in VA_CMD_LIST.items():
        for x in v:
            vrt = fuzz.ratio(cmd, x)
            if vrt > rc['percent']:
                rc['cmd'] = c
                rc['percent'] = vrt
    return rc

def run_applescript(script):
    """Helper function to run AppleScript commands"""
    try:
        osascript.osascript(script)
        return True
    except Exception as e:
        print(f"AppleScript error: {e}")
        return False

def get_weather(city="Moscow"):
    """Get weather information"""
    try:
        # You can use a weather API here, for now using a mock response
        return f"В городе {city} сейчас переменная облачность, температура около 20 градусов"
    except:
        return "Не удалось получить информацию о погоде"

def search_web(query):
    """Search the web"""
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(search_url)
        return True
    except:
        return False

def execute_cmd(cmd: str, voice: str):
    print(f"🔧 Выполнение команды: {cmd}")
    
    # Browser commands
    if cmd == 'open_browser':
        subprocess.Popen(['open', '/Applications/Google Chrome.app'])
        play("ok")

    elif cmd == 'open_youtube':
        webbrowser.open('https://youtube.com')
        play("ok")

    elif cmd == 'open_google':
        webbrowser.open('https://google.com')
        play("ok")

    # Music commands
    elif cmd == 'music':
        script = '''
        tell application "Music"
            activate
            play
        end tell
        '''
        if run_applescript(script):
            play("ok")
            tts.va_speak("Включаю музыку")
        else:
            subprocess.Popen(['open', '/Applications/Spotify.app'])
            play("ok")

    elif cmd == 'music_off':
        script = '''
        tell application "Music"
            pause
        end tell
        '''
        run_applescript(script)
        play("ok")
        tts.va_speak("Музыка остановлена")

    elif cmd == 'music_next':
        script = '''
        tell application "Music"
            next track
        end tell
        '''
        run_applescript(script)
        play("ok")

    elif cmd == 'music_prev':
        script = '''
        tell application "Music"
            previous track
        end tell
        '''
        run_applescript(script)
        play("ok")

    elif cmd == 'music_save':
        script = '''
        tell application "Music"
            set current_track to current track
            add current_track to playlist "Favorites"
        end tell
        '''
        run_applescript(script)
        play("ok")
        tts.va_speak("Песня добавлена в избранное")

    # Volume commands
    elif cmd == 'sound_off':
        play("ok", True)
        subprocess.run(['osascript', '-e', 'set volume output muted true'])

    elif cmd == 'sound_on':
        subprocess.run(['osascript', '-e', 'set volume output muted false'])
        play("ok")

    elif cmd == 'volume_up':
        subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) + 10)'])
        play("ok")

    elif cmd == 'volume_down':
        subprocess.run(['osascript', '-e', 'set volume output volume (output volume of (get volume settings) - 10)'])
        play("ok")

    # Applications
    elif cmd == 'open_finder':
        subprocess.Popen(['open', '/System/Library/CoreServices/Finder.app'])
        play("ok")

    elif cmd == 'open_terminal':
        subprocess.Popen(['open', '/Applications/Utilities/Terminal.app'])
        play("ok")

    elif cmd == 'open_calculator':
        subprocess.Popen(['open', '/Applications/Calculator.app'])
        play("ok")

    elif cmd == 'open_notes':
        subprocess.Popen(['open', '/Applications/Notes.app'])
        play("ok")

    elif cmd == 'open_calendar':
        subprocess.Popen(['open', '/Applications/Calendar.app'])
        play("ok")

    elif cmd == 'open_mail':
        subprocess.Popen(['open', '/Applications/Mail.app'])
        play("ok")

    # System commands
    elif cmd == 'screenshot':
        subprocess.run(['screencapture', '-c'])  # Screenshot to clipboard
        play("ok")
        tts.va_speak("Скриншот сохранен в буфер обмена")

    elif cmd == 'lock_screen':
        subprocess.run(['/System/Library/CoreServices/Menu Extras/User.menu/Contents/Resources/CGSession', '-suspend'])
        play("ok")

    elif cmd == 'sleep_mode':
        subprocess.run(['pmset', 'sleepnow'])
        play("ok")

    # Information commands
    elif cmd == 'what_time':
        current_time = datetime.datetime.now().strftime("%H:%M")
        play("ok")
        tts.va_speak(f"Сейчас {current_time}")

    elif cmd == 'what_date':
        current_date = datetime.datetime.now().strftime("%d %B %Y года")
        play("ok")
        tts.va_speak(f"Сегодня {current_date}")

    elif cmd == 'weather':
        weather_info = get_weather()
        play("ok")
        tts.va_speak(weather_info)

    elif cmd == 'search_web':
        # Extract search query from voice
        query = voice.replace("найди в интернете", "").replace("поиск в сети", "").replace("загугли", "").strip()
        if query:
            if search_web(query):
                play("ok")
                tts.va_speak(f"Ищу информацию о {query}")
            else:
                play("error")
        else:
            tts.va_speak("Что именно найти?")

    # Entertainment
    elif cmd == 'tell_joke':
        jokes = [
            "Почему программисты не любят природу? Потому что там слишком много багов!",
            "Я не глючу, я просто имею недокументированные возможности!",
            "10 видов людей: те кто понимают двоичную систему и те кто не понимают!"
        ]
        joke = random.choice(jokes)
        play("ok")
        tts.va_speak(joke)

    # Social commands
    elif cmd == 'thanks':
        play("thanks")
        responses = ["Всегда рад помочь!", "Обращайтесь!", "К вашим услугам!"]
        tts.va_speak(random.choice(responses))

    elif cmd == 'stupid':
        play("stupid")
        responses = ["Я всего лишь учусь", "Может быть стоит обновить мои алгоритмы?", "Извините, сэр"]
        tts.va_speak(random.choice(responses))

    elif cmd == 'compliment':
        play("thanks")
        responses = ["Спасибо за оценку!", "Стараюсь быть полезным!", "Приятно слышать!"]
        tts.va_speak(random.choice(responses))

    # Work modes
    elif cmd == 'focus_mode':
        script = '''
        tell application "System Events"
            tell process "Control Center"
                -- Enable Focus mode
            end tell
        end tell
        '''
        play("ok")
        tts.va_speak("Режим концентрации включен")

    elif cmd == 'gaming_mode_on':
        play("ok")
        subprocess.run(['shortcuts', 'run', 'Gaming Mode On'], capture_output=True)
        play("ready")
        tts.va_speak("Игровой режим активирован")

    elif cmd == 'gaming_mode_off':
        play("ok")
        subprocess.run(['shortcuts', 'run', 'Gaming Mode Off'], capture_output=True)
        play("ready")
        tts.va_speak("Обычный режим восстановлен")

    # Audio devices
    elif cmd == 'switch_to_headphones':
        play("ok")
        # This would need specific AppleScript for your audio setup
        script = '''
        tell application "System Preferences"
            activate
            set current pane to pane "Sound"
        end tell
        '''
        run_applescript(script)
        tts.va_speak("Переключаюсь на наушники")

    elif cmd == 'switch_to_dynamics':
        play("ok")
        tts.va_speak("Переключаюсь на динамики")

    # Smart features commands
    elif cmd == 'system_status' and smart_features:
        play("working")
        status = smart_features.get_system_status()
        tts.va_speak(status)

    elif cmd == 'running_apps' and smart_features:
        play("working")
        apps = smart_features.get_running_apps()
        if apps:
            apps_text = "Запущенные приложения: " + ", ".join(apps[:5])
            tts.va_speak(apps_text)
        else:
            tts.va_speak("Не удалось получить список приложений")

    elif cmd == 'wifi_info' and smart_features:
        play("working")
        wifi_info = smart_features.get_wifi_info()
        tts.va_speak(wifi_info)

    elif cmd == 'productivity_stats' and smart_features:
        play("working")
        stats = smart_features.productivity_stats()
        tts.va_speak(stats)

    elif cmd == 'create_reminder' and smart_features:
        # Extract reminder text from voice
        reminder_text = voice.replace("создай напоминание", "").replace("напомни мне", "").strip()
        if reminder_text:
            result = smart_features.create_reminder(reminder_text)
            play("ok")
            tts.va_speak(result)
        else:
            tts.va_speak("О чем напомнить?")

    elif cmd == 'create_note' and smart_features:
        # Extract note text from voice
        note_text = voice.replace("создай заметку", "").replace("запиши", "").strip()
        if note_text:
            result = smart_features.create_note(note_text)
            play("ok")
            tts.va_speak(result)
        else:
            tts.va_speak("Что записать?")

    elif cmd == 'calendar_events' and smart_features:
        play("working")
        events = smart_features.get_calendar_events()
        tts.va_speak(events)

    elif cmd == 'set_timer' and smart_features:
        # Extract timer duration from voice
        import re
        numbers = re.findall(r'\d+', voice)
        if numbers:
            minutes = int(numbers[0])
            result = smart_features.set_timer(minutes)
            play("ok")
            tts.va_speak(result)
        else:
            tts.va_speak("На сколько минут поставить таймер?")

    elif cmd == 'search_files' and smart_features:
        # Extract filename from voice
        filename = voice.replace("найди файл", "").replace("ищи файл", "").replace("где файл", "").strip()
        if filename:
            result = smart_features.search_files(filename)
            play("ok")
            tts.va_speak(result)
        else:
            tts.va_speak("Какой файл найти?")

    elif cmd == 'get_definition' and smart_features:
        # Extract word from voice
        word = voice.replace("что означает", "").replace("определение слова", "").replace("что такое", "").strip()
        if word:
            definition = smart_features.get_definition(word)
            play("ok")
            tts.va_speak(definition)
        else:
            tts.va_speak("Определение какого слова найти?")

    elif cmd == 'calculate' and smart_features:
        # Extract mathematical expression
        expression = voice.replace("посчитай", "").replace("вычисли", "").replace("сколько будет", "").strip()
        if expression:
            result = smart_features.calculate_expression(expression)
            play("ok")
            tts.va_speak(result)
        else:
            tts.va_speak("Что посчитать?")

    elif cmd == 'get_news' and smart_features:
        play("working")
        news = smart_features.get_top_news()
        tts.va_speak(news)

    elif cmd == 'emergency_contacts' and smart_features:
        play("ok")
        contacts = smart_features.emergency_contacts()
        tts.va_speak(contacts)

    # Spotify commands
    elif cmd == 'spotify_play' and smart_features:
        result = smart_features.control_spotify('play')
        play("ok")
        tts.va_speak(result)

    elif cmd == 'spotify_pause' and smart_features:
        result = smart_features.control_spotify('pause')
        play("ok")
        tts.va_speak(result)

    elif cmd == 'off':
        play("off", True)
        goodbye_messages = [
            "До свидания, сэр!",
            "Завершаю работу!",
            "Увидимся позже!",
            "Хорошего дня!"
        ]
        tts.va_speak(random.choice(goodbye_messages))
        porcupine.delete()
        pygame.mixer.quit()
        exit(0)

# Initialize recorder
recorder = PvRecorder(device_index=config.MICROPHONE_INDEX, frame_length=porcupine.frame_length)
recorder.start()
print('🎙️  Using device: %s' % recorder.selected_device)

print(f"🤖 Jarvis Enhanced (v3.1) запущен на macOS...")
print("📱 Доступные функции:")
print("   • Управление музыкой и звуком")
print("   • Открытие приложений")
print("   • Системные команды")
print("   • Поиск в интернете")
print("   • Информация о времени и погоде")
print("   • AI-диалоги")

startup_messages = [
    "Системы загружены, готов к работе!",
    "Джарвис к вашим услугам!",
    "Все системы в норме, жду команд!"
]

play("run")
time.sleep(0.5)
tts.va_speak(random.choice(startup_messages))

ltc = time.time() - 1000

while True:
    try:
        pcm = recorder.read()
        keyword_index = porcupine.process(pcm)

        if keyword_index >= 0:
            recorder.stop()
            play("greet", True)
            print("🔥 Yes, sir.")
            recorder.start()
            ltc = time.time()

        while time.time() - ltc <= 10:
            pcm = recorder.read()
            sp = struct.pack("h" * len(pcm), *pcm)

            if kaldi_rec.AcceptWaveform(sp):
                if va_respond(json.loads(kaldi_rec.Result())["text"]):
                    ltc = time.time()
                break

    except Exception as err:
        print(f"❌ Unexpected {err=}, {type(err)=}")
        play("error")
        time.sleep(1)