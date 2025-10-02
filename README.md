# 📱 Instagram & TikTok Downloader API

Простой REST API для скачивания видео из Instagram и TikTok с автоматическим управлением файлами.

## 🎯 Что это такое?

Это веб-сервис, который:
- 📥 **Скачивает видео** из Instagram Reels и TikTok
- 💾 **Сохраняет файлы** на сервер с автоматической очисткой
- 📊 **Извлекает метаданные** (автор, описание, дата)
- 🔄 **Управляет дисковым пространством** (хранит только последние 10 видео)

## 🚀 Быстрый старт

### 1. Установка
```bash
# Клонируйте проект
git clone <repository-url>
cd insta_downloader

# Создайте виртуальное окружение
python -m venv .venv

# Активируйте виртуальное окружение
source .venv/bin/activate

# Установите зависимости (если нужно)
pip install -r requirements.txt
```

### 2. Настройка Instagram
```bash
# Создайте файл сессии для Instagram
# Поместите .instaloader-session в корень проекта
```

### 3. Запуск сервера

#### 🚀 Простой способ (рекомендуется)
```bash
# Запуск сервера
make start

# Остановка сервера
make stop

# Перезагрузка сервера
make restart

# Проверка статуса
make status
```

#### 🔧 Ручной способ
```bash
# Запустите сервер
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Сервер будет доступен по адресу: `http://localhost:8000`

## 🎛️ Управление сервером

### 📋 Основные команды

| Команда | Описание | Пример |
|---------|----------|--------|
| `make start` | Запустить сервер | `make start` |
| `make stop` | Остановить сервер | `make stop` |
| `make restart` | Перезапустить сервер | `make restart` |
| `make status` | Проверить статус | `make status` |
| `make help` | Показать все команды | `make help` |

### 🔧 Дополнительные команды

| Команда | Описание |
|---------|----------|
| `make clean` | Очистить временные файлы |
| `make install` | Установить зависимости |
| `make test` | Запустить тесты |
| `make dev` | Запуск в режиме разработки |
| `make prod` | Запуск в продакшн режиме |
| `make logs` | Показать логи в реальном времени |
| `make kill` | Принудительно остановить все процессы |

### 📊 Проверка статуса сервера

```bash
# Проверить статус
make status

# Вывод:
# 📊 Instagram Downloader API Server Status
# ==================================================
# ✅ Server is RUNNING
# 📝 PID: 12345
# 🌐 Port: 8000
# 🌐 URL: http://localhost:8000
# ✅ Port is active
# 📄 Log file: /path/to/logs/app.log
# 📅 Last modified: Thu Oct 2 16:30:49 2025
# ==================================================
```

### 🚨 Экстренная остановка

Если сервер не останавливается обычными способами:

```bash
# Принудительная остановка всех процессов
make kill

# Или вручную
pkill -f "uvicorn app.main:app"
lsof -ti:8000 | xargs -r kill -9
```

### 📝 Логи сервера

```bash
# Просмотр логов в реальном времени
make logs

# Или напрямую
tail -f logs/app.log
```

## 📡 REST API

### 🎬 Скачивание видео

**Endpoint:** `POST /api/download/`

**Описание:** Скачивает видео из Instagram или TikTok по ссылке

#### 📝 Запрос

```bash
curl -X POST "http://localhost:8000/api/download/" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reel/DPFJiwpDiBL/"
  }'
```

#### 📤 Ответ

```json
{
  "author": "username",
  "description": "Полное описание видео с переносами строк",
  "created_at": "2025-09-30T14:23:00",
  "video_url": "http://localhost:8000/static/video123.mp4"
}
```

#### 📋 Параметры запроса

| Поле | Тип | Обязательно | Описание |
|------|-----|-------------|----------|
| `url` | string | ✅ | Ссылка на Instagram Reel или TikTok видео |

#### 📊 Поля ответа

| Поле | Тип | Описание |
|------|-----|----------|
| `author` | string | Имя автора поста |
| `description` | string | Полное описание видео |
| `created_at` | string | Дата создания (ISO формат) |
| `video_url` | string | Публичная ссылка на скачанное видео |

## 🔗 Поддерживаемые ссылки

### ✅ Instagram
- `https://www.instagram.com/reel/DPFJiwpDiBL/`
- `https://www.instagram.com/p/DPFJiwpDiBL/`
- `https://instagram.com/reel/DPFJiwpDiBL/?utm_source=ig_web_copy_link`

### ✅ TikTok
- `https://www.tiktok.com/@user/video/1234567890`
- `https://vm.tiktok.com/ZMAac7Uhm/`
- `https://tiktok.com/@username/video/1234567890`

## 📁 Структура файлов

```
insta_downloader/
├── app/
│   ├── main.py                    # Основной файл приложения
│   ├── server_manager.py          # 🆕 Менеджер сервера
│   ├── routers/
│   │   └── download.py            # API маршруты
│   ├── services/
│   │   ├── instagram_service.py   # Instagram скачивание
│   │   └── tiktok_service.py      # TikTok скачивание
│   ├── media/                     # Скачанные видео (автоочистка)
│   └── static/                    # Публичные файлы
├── logs/
│   └── app.log                    # Логи приложения
├── Makefile                       # 🆕 Команды управления сервером
├── server.pid                     # 🆕 PID файл сервера (автоматически)
└── .instaloader-session           # Instagram сессия
```

## ⚙️ Особенности

### 🔄 Автоматическая очистка файлов
- **Лимит:** максимум 10 последних видео
- **Очистка:** автоматически после каждого скачивания
- **Сортировка:** по времени модификации (новые сохраняются)

### 📝 Логирование
- **Файл:** `logs/app.log`
- **Режим:** реальное время
- **Содержит:** процесс скачивания, ошибки, очистку файлов

### 🔐 Авторизация Instagram
- **Файл сессии:** `.instaloader-session`
- **Расположение:** корень проекта
- **Автоматическая:** при запуске сервера

## 🚨 Обработка ошибок

### ❌ Частые ошибки

| Код | Описание | Решение |
|-----|----------|---------|
| `400` | Неверный URL | Проверьте формат ссылки |
| `403` | Приватный контент | Настройте Instagram авторизацию |
| `404` | Видео не найдено | Проверьте доступность ссылки |
| `500` | Ошибка сервера | Проверьте логи в `app.log` |

### 📋 Примеры ошибок

```json
{
  "detail": "Instagram returned 403/authorization error. The content may be private or restricted."
}
```

```json
{
  "detail": "Error downloading TikTok video: Could not resolve TikTok video URL"
}
```

## 🔧 Настройка

### 📊 Изменение лимита файлов
В файлах сервисов измените значение:
```python
self.max_files = 10  # Измените на нужное количество
```

### 📝 Уровень логирования
В `app/main.py` настройте уровень:
```python
logging.basicConfig(level=logging.INFO)  # INFO, DEBUG, WARNING, ERROR
```

## 📈 Мониторинг

### 📊 Проверка статуса
```bash
# Проверьте логи
tail -f logs/app.log

# Проверьте количество файлов
ls -la app/media/*.mp4 | wc -l

# Проверьте размер папки
du -sh app/media/
```

### 🔍 Отладка
```bash
# Запуск с подробными логами
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level debug
```

## 🎯 Примеры использования

### 📱 Instagram Reel
```bash
curl -X POST "http://localhost:8000/api/download/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.instagram.com/reel/DPFJiwpDiBL/"}'
```

### 🎵 TikTok видео
```bash
curl -X POST "http://localhost:8000/api/download/" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://vm.tiktok.com/ZMAac7Uhm/"}'
```

## 🛠️ Технические детали

- **Framework:** FastAPI
- **Instagram:** instaloader
- **TikTok:** yt-dlp
- **Python:** 3.9+
- **Порт:** 8000

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи в `logs/app.log`
2. Убедитесь в правильности Instagram сессии
3. Проверьте доступность ссылок
4. Убедитесь в наличии свободного места на диске

---

**Готово к использованию!** 🚀
