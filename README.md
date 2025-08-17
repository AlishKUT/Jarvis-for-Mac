# 🤖 Jarvis for Mac (Python Version)

Адаптированная версия проекта [Howdyho Jarvis](https://github.com/Priler/jarvis), полностью переписанная под **macOS** и Python.  
Добавлены новые **Smart Features**, заменён движок с OpenAI → на **Google Gemini** (так как бесплатный).  

Все настройки вынесены в `.env` для удобного управления API-ключами.  
Список доступных команд можно найти в файле **`commands.yaml`**.  

---

## 🚀 Установка и запуск

### 1. Клонирование проекта
```bash
git clone https://github.com/AlishKUT/Jarvis-for-Mac.git
cd Jarvis-for-Mac

Создание и активация виртуального окружения

```bash
python3 -m venv venv
source venv/bin/activate   # для macOS/Linux

Установка зависимостей

```bash
pip install -r requirements.txt

Замените ключ 

GEMINI_API_KEY=ваш_ключ_от_Google_Gemini

Запуск

```bash
python main.py
