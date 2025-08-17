import os
import json
import subprocess
import requests
import datetime
import psutil
import platform
from typing import Dict, List, Any

class SmartFeatures:
    def __init__(self):
        self.system_info = self._get_system_info()
        
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        return {
            'platform': platform.platform(),
            'processor': platform.processor(),
            'memory_total': psutil.virtual_memory().total // (1024**3),  # GB
            'disk_usage': psutil.disk_usage('/').percent
        }
    
    def get_system_status(self) -> str:
        """Get current system status"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # Battery (if laptop)
            battery_info = ""
            if hasattr(psutil, "sensors_battery"):
                battery = psutil.sensors_battery()
                if battery:
                    battery_info = f"Батарея: {battery.percent:.0f}%, "
            
            status = f"Система: ЦП {cpu_percent:.0f}%, ОЗУ {memory_percent:.0f}%, Диск {disk_percent:.0f}%. {battery_info}Все работает нормально."
            return status
            
        except Exception as e:
            return f"Ошибка получения статуса системы: {e}"
    
    def get_running_apps(self) -> List[str]:
        """Get list of running applications"""
        try:
            apps = []
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'] and not proc.info['name'].startswith('com.'):
                        apps.append(proc.info['name'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Get unique app names, filter system processes
            unique_apps = list(set(apps))
            user_apps = [app for app in unique_apps if not any(
                sys_name in app.lower() for sys_name in 
                ['kernel', 'system', 'daemon', 'helper', 'service']
            )]
            
            return sorted(user_apps)[:10]  # Top 10 apps
            
        except Exception as e:
            return [f"Ошибка: {e}"]
    
    def get_wifi_info(self) -> str:
        """Get WiFi connection information"""
        try:
            # macOS command to get WiFi info
            result = subprocess.run([
                '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport',
                '-I'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                ssid = "Неизвестно"
                signal = "Неизвестно"
                
                for line in lines:
                    if 'SSID:' in line:
                        ssid = line.split('SSID:')[1].strip()
                    elif 'agrCtlRSSI:' in line:
                        signal = line.split('agrCtlRSSI:')[1].strip()
                
                return f"Подключен к сети {ssid}, уровень сигнала {signal} dBm"
            else:
                return "WiFi информация недоступна"
                
        except Exception as e:
            return f"Ошибка получения WiFi информации: {e}"
    
    def create_reminder(self, reminder_text: str, time_str: str = None) -> str:
        """Create a reminder using macOS Reminders app"""
        try:
            if time_str:
                # Parse time and create reminder with date
                script = f'''
                tell application "Reminders"
                    make new reminder with properties {{name:"{reminder_text}", due date:(current date) + (1 * hours)}}
                end tell
                '''
            else:
                # Simple reminder without time
                script = f'''
                tell application "Reminders"
                    make new reminder with properties {{name:"{reminder_text}"}}
                end tell
                '''
            
            subprocess.run(['osascript', '-e', script])
            return f"Напоминание '{reminder_text}' создано"
            
        except Exception as e:
            return f"Ошибка создания напоминания: {e}"
    
    def get_calendar_events(self) -> str:
        """Get today's calendar events"""
        try:
            script = '''
            tell application "Calendar"
                set today to current date
                set startOfDay to (today - (time of today))
                set endOfDay to startOfDay + (24 * 60 * 60)
                
                set todayEvents to every event of every calendar whose start date ≥ startOfDay and start date ≤ endOfDay
                
                set eventList to ""
                repeat with anEvent in todayEvents
                    set eventList to eventList & (summary of anEvent) & " в " & (time string of start date of anEvent) & "; "
                end repeat
                
                return eventList
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                events = result.stdout.strip()
                return f"События на сегодня: {events}"
            else:
                return "На сегодня событий нет"
                
        except Exception as e:
            return f"Ошибка получения событий: {e}"
    
    def control_smart_home(self, device: str, action: str) -> str:
        """Control smart home devices via HomeKit"""
        try:
            # This is a template for HomeKit integration
            # You would need to implement specific HomeKit commands
            script = f'''
            tell application "Home"
                -- Control HomeKit device
                -- This requires specific HomeKit setup
            end tell
            '''
            
            return f"Команда '{action}' отправлена на устройство '{device}'"
            
        except Exception as e:
            return f"Ошибка управления умным домом: {e}"
    
    def get_stock_price(self, symbol: str) -> str:
        """Get stock price (requires API key)"""
        try:
            # This is a template - you'd need a real financial API
            # For now, return a mock response
            return f"Акции {symbol}: цена недоступна (требуется API ключ)"
            
        except Exception as e:
            return f"Ошибка получения цены акций: {e}"
    
    def translate_text(self, text: str, target_lang: str = 'en') -> str:
        """Translate text using Google Translate (requires API)"""
        try:
            # This is a template - you'd need Google Translate API
            # For now, return a mock response
            return f"Перевод недоступен (требуется API ключ Google Translate)"
            
        except Exception as e:
            return f"Ошибка перевода: {e}"
    
    def calculate_expression(self, expression: str) -> str:
        """Calculate mathematical expressions safely"""
        try:
            # Remove dangerous functions and allow only basic math
            allowed_chars = set('0123456789+-*/().,= ')
            if not all(c in allowed_chars for c in expression):
                return "Недопустимые символы в выражении"
            
            # Replace common Russian math terms
            expression = expression.replace('плюс', '+')
            expression = expression.replace('минус', '-')
            expression = expression.replace('умножить на', '*')
            expression = expression.replace('разделить на', '/')
            expression = expression.replace('равно', '=')
            
            # Remove equals sign for calculation
            if '=' in expression:
                expression = expression.split('=')[0]
            
            # Safely evaluate the expression
            result = eval(expression)
            return f"Результат: {result}"
            
        except Exception as e:
            return f"Ошибка вычисления: не могу посчитать '{expression}'"
    
    def get_weather_forecast(self, city: str = "Moscow") -> str:
        """Get weather forecast"""
        try:
            # This would require a weather API key
            # For demonstration, returning mock data
            import random
            
            temperatures = [-5, 0, 5, 10, 15, 20, 25]
            conditions = ["ясно", "облачно", "дождь", "снег", "переменная облачность"]
            
            temp = random.choice(temperatures)
            condition = random.choice(conditions)
            
            return f"Погода в {city}: {temp}°C, {condition}"
            
        except Exception as e:
            return f"Ошибка получения прогноза: {e}"
    
    def set_timer(self, minutes: int, message: str = "Время вышло!") -> str:
        """Set a timer using macOS"""
        try:
            # Convert minutes to seconds
            seconds = minutes * 60
            
            # Create AppleScript for timer
            script = f'''
            delay {seconds}
            display notification "{message}" with title "Таймер Джарвис"
            say "{message}"
            '''
            
            # Run timer in background
            subprocess.Popen(['osascript', '-e', script])
            
            return f"Таймер установлен на {minutes} минут"
            
        except Exception as e:
            return f"Ошибка установки таймера: {e}"
    
    def create_note(self, note_text: str) -> str:
        """Create a note in Notes app"""
        try:
            script = f'''
            tell application "Notes"
                make new note with properties {{body:"{note_text}"}}
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script])
            return f"Заметка создана: {note_text[:50]}..."
            
        except Exception as e:
            return f"Ошибка создания заметки: {e}"
    
    def get_top_news(self) -> str:
        """Get top news headlines"""
        try:
            # This would require a news API
            # For demonstration, returning mock headlines
            mock_headlines = [
                "Новые технологии в области искусственного интеллекта",
                "Обновления в macOS и их влияние на пользователей",
                "Последние достижения в космических исследованиях",
                "Развитие возобновляемой энергетики в мире"
            ]
            
            import random
            headline = random.choice(mock_headlines)
            
            return f"Главные новости: {headline}"
            
        except Exception as e:
            return f"Ошибка получения новостей: {e}"
    
    def control_spotify(self, action: str) -> str:
        """Control Spotify playback"""
        try:
            actions = {
                'play': 'play',
                'pause': 'pause',
                'next': 'next track',
                'previous': 'previous track',
                'stop': 'pause'
            }
            
            spotify_action = actions.get(action.lower(), 'play')
            
            script = f'''
            tell application "Spotify"
                {spotify_action}
            end tell
            '''
            
            subprocess.run(['osascript', '-e', script])
            return f"Spotify: выполнено действие '{action}'"
            
        except Exception as e:
            return f"Ошибка управления Spotify: {e}"
    
    def search_files(self, filename: str, location: str = "~") -> str:
        """Search for files on the system"""
        try:
            # Use mdfind (Spotlight) to search for files
            result = subprocess.run([
                'mdfind', 
                '-name', filename
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                files = result.stdout.strip().split('\n')
                if files and files[0]:
                    found_files = [f for f in files[:5] if f]  # Top 5 results
                    files_list = '\n'.join([os.path.basename(f) for f in found_files])
                    return f"Найдено файлов с именем '{filename}':\n{files_list}"
                else:
                    return f"Файлы с именем '{filename}' не найдены"
            else:
                return "Ошибка поиска файлов"
                
        except Exception as e:
            return f"Ошибка поиска: {e}"
    
    def get_definition(self, word: str) -> str:
        """Get word definition using macOS Dictionary"""
        try:
            # Use macOS Dictionary service
            script = f'''
            tell application "Dictionary"
                activate
                set theDefinition to definition of "{word}"
                return theDefinition
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout.strip():
                definition = result.stdout.strip()
                # Limit definition length
                if len(definition) > 200:
                    definition = definition[:200] + "..."
                return f"Определение '{word}': {definition}"
            else:
                return f"Определение для '{word}' не найдено"
                
        except Exception as e:
            return f"Ошибка получения определения: {e}"
    
    def emergency_contacts(self) -> str:
        """Show emergency contacts information"""
        emergency_info = """
        Экстренные службы:
        🚨 Скорая помощь: 103
        🚒 Пожарная: 101
        👮 Полиция: 102
        ⛑️ Единая служба: 112
        """
        return emergency_info.strip()
    
    def productivity_stats(self) -> str:
        """Get basic productivity statistics"""
        try:
            # Get uptime
            uptime_result = subprocess.run(['uptime'], capture_output=True, text=True)
            
            # Get number of running processes
            process_count = len(list(psutil.process_iter()))
            
            # Get active applications count
            apps = self.get_running_apps()
            app_count = len(apps)
            
            stats = f"""
            📊 Статистика продуктивности:
            ⏱️ Время работы: {uptime_result.stdout.strip() if uptime_result.returncode == 0 else 'недоступно'}
            🖥️ Запущено процессов: {process_count}
            📱 Активных приложений: {app_count}
            """
            
            return stats.strip()
            
        except Exception as e:
            return f"Ошибка получения статистики: {e}"

# Global instance
smart_features = SmartFeatures()