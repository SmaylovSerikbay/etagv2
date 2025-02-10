from .base import *

# Импортируем production настройки только если установлена соответствующая переменная окружения
import os
if os.environ.get('DJANGO_SETTINGS_MODULE') == 'etag.settings.production':
    from .production import * 