"""
Утилиты для работы с содержимым виджетов
"""

def get_display_content(content, widget_type):
    """
    Преобразует содержимое виджета в удобочитаемый вид для отображения в формах редактирования
    
    Args:
        content (str): Исходное содержимое виджета
        widget_type (str): Тип виджета
    
    Returns:
        str: Удобочитаемое содержимое
    """
    if not content:
        return content
    
    # Телефонные номера
    if content.startswith('tel:'):
        return content[4:]  # Убираем tel:
    
    # SMS
    if content.startswith('sms:'):
        return content[4:]  # Убираем sms:
    
    # Email
    if content.startswith('mailto:'):
        return content[7:]  # Убираем mailto:
    
    # YouTube
    if content.startswith('https://youtube.com/@'):
        return content[21:]  # Убираем https://youtube.com/@
    if content.startswith('https://www.youtube.com/@'):
        return content[25:]  # Убираем https://www.youtube.com/@
    if content.startswith('https://youtube.com/c/'):
        return content[20:]  # Убираем https://youtube.com/c/
    if content.startswith('https://www.youtube.com/c/'):
        return content[24:]  # Убираем https://www.youtube.com/c/
    if content.startswith('https://youtube.com/channel/'):
        return content[28:]  # Убираем https://youtube.com/channel/
    if content.startswith('https://www.youtube.com/channel/'):
        return content[32:]  # Убираем https://www.youtube.com/channel/
    
    # Instagram
    if content.startswith('https://instagram.com/'):
        return content[21:]  # Убираем https://instagram.com/
    if content.startswith('https://www.instagram.com/'):
        return content[25:]  # Убираем https://www.instagram.com/
    
    # TikTok
    if content.startswith('https://tiktok.com/@'):
        return content[19:]  # Убираем https://tiktok.com/@
    if content.startswith('https://www.tiktok.com/@'):
        return content[23:]  # Убираем https://www.tiktok.com/@
    
    # Telegram
    if content.startswith('https://t.me/'):
        return content[13:]  # Убираем https://t.me/
    
    # WhatsApp
    if content.startswith('https://wa.me/'):
        return content[13:]  # Убираем https://wa.me/
    
    # Facebook
    if content.startswith('https://facebook.com/'):
        return content[20:]  # Убираем https://facebook.com/
    if content.startswith('https://www.facebook.com/'):
        return content[24:]  # Убираем https://www.facebook.com/
    
    # LinkedIn
    if content.startswith('https://linkedin.com/in/'):
        return content[22:]  # Убираем https://linkedin.com/in/
    if content.startswith('https://www.linkedin.com/in/'):
        return content[26:]  # Убираем https://www.linkedin.com/in/
    
    # Twitter/X
    if content.startswith('https://twitter.com/'):
        return content[20:]  # Убираем https://twitter.com/
    if content.startswith('https://www.twitter.com/'):
        return content[24:]  # Убираем https://www.twitter.com/
    if content.startswith('https://x.com/'):
        return content[13:]  # Убираем https://x.com/
    if content.startswith('https://www.x.com/'):
        return content[17:]  # Убираем https://www.x.com/
    
    # VK
    if content.startswith('https://vk.com/'):
        return content[15:]  # Убираем https://vk.com/
    if content.startswith('https://www.vk.com/'):
        return content[19:]  # Убираем https://www.vk.com/
    
    # Одноклассники
    if content.startswith('https://ok.ru/'):
        return content[14:]  # Убираем https://ok.ru/
    if content.startswith('https://www.ok.ru/'):
        return content[18:]  # Убираем https://www.ok.ru/
    
    # Snapchat
    if content.startswith('https://snapchat.com/add/'):
        return content[25:]  # Убираем https://snapchat.com/add/
    if content.startswith('https://www.snapchat.com/add/'):
        return content[29:]  # Убираем https://www.snapchat.com/add/
    
    # Pinterest
    if content.startswith('https://pinterest.com/'):
        return content[21:]  # Убираем https://pinterest.com/
    if content.startswith('https://www.pinterest.com/'):
        return content[25:]  # Убираем https://www.pinterest.com/
    
    # Behance
    if content.startswith('https://behance.net/'):
        return content[19:]  # Убираем https://behance.net/
    if content.startswith('https://www.behance.net/'):
        return content[23:]  # Убираем https://www.behance.net/
    
    # 500px
    if content.startswith('https://500px.com/'):
        return content[17:]  # Убираем https://500px.com/
    if content.startswith('https://www.500px.com/'):
        return content[21:]  # Убираем https://www.500px.com/
    
    # Twitch
    if content.startswith('https://twitch.tv/'):
        return content[17:]  # Убираем https://twitch.tv/
    if content.startswith('https://www.twitch.tv/'):
        return content[21:]  # Убираем https://www.twitch.tv/
    
    # Discord
    if content.startswith('https://discord.gg/'):
        return content[18:]  # Убираем https://discord.gg/
    if content.startswith('https://discord.com/invite/'):
        return content[26:]  # Убираем https://discord.com/invite/
    
    # Steam
    if content.startswith('https://steamcommunity.com/id/'):
        return content[30:]  # Убираем https://steamcommunity.com/id/
    if content.startswith('https://steamcommunity.com/profiles/'):
        return content[35:]  # Убираем https://steamcommunity.com/profiles/
    
    # App Store
    if content.startswith('https://apps.apple.com/'):
        return content[23:]  # Убираем https://apps.apple.com/
    
    # Google Play
    if content.startswith('https://play.google.com/store/apps/'):
        return content[35:]  # Убираем https://play.google.com/store/apps/
    
    # Spotify
    if content.startswith('https://open.spotify.com/'):
        return content[25:]  # Убираем https://open.spotify.com/
    
    # Apple Music
    if content.startswith('https://music.apple.com/'):
        return content[24:]  # Убираем https://music.apple.com/
    
    # SoundCloud
    if content.startswith('https://soundcloud.com/'):
        return content[23:]  # Убираем https://soundcloud.com/
    
    # Яндекс Музыка
    if content.startswith('https://music.yandex.ru/'):
        return content[24:]  # Убираем https://music.yandex.ru/
    if content.startswith('https://music.yandex.com/'):
        return content[24:]  # Убираем https://music.yandex.com/
    
    # VK Музыка
    if content.startswith('https://vk.com/audio/'):
        return content[20:]  # Убираем https://vk.com/audio/
    
    # Boom
    if content.startswith('https://boom.ru/'):
        return content[16:]  # Убираем https://boom.ru/
    if content.startswith('https://www.boom.ru/'):
        return content[20:]  # Убираем https://www.boom.ru/
    
    # Сбер Звук
    if content.startswith('https://sber-zvuk.com/'):
        return content[21:]  # Убираем https://sber-zvuk.com/
    if content.startswith('https://www.sber-zvuk.com/'):
        return content[25:]  # Убираем https://www.sber-zvuk.com/
    
    # YouTube Music
    if content.startswith('https://music.youtube.com/'):
        return content[26:]  # Убираем https://music.youtube.com/
    
    # Яндекс Дзен
    if content.startswith('https://zen.yandex.ru/'):
        return content[22:]  # Убираем https://zen.yandex.ru/
    if content.startswith('https://zen.yandex.com/'):
        return content[22:]  # Убираем https://zen.yandex.com/
    
    # Kwaii
    if content.startswith('https://kwai.com/'):
        return content[17:]  # Убираем https://kwai.com/
    if content.startswith('https://www.kwai.com/'):
        return content[21:]  # Убираем https://www.kwai.com/
    
    # Likee
    if content.startswith('https://likee.video/'):
        return content[19:]  # Убираем https://likee.video/
    if content.startswith('https://www.likee.video/'):
        return content[23:]  # Убираем https://www.likee.video/
    
    # WeChat
    if content.startswith('https://weixin.qq.com/'):
        return content[21:]  # Убираем https://weixin.qq.com/
    
    # YCLIENTS
    if content.startswith('https://yclients.com/'):
        return content[20:]  # Убираем https://yclients.com/
    if content.startswith('https://www.yclients.com/'):
        return content[24:]  # Убираем https://www.yclients.com/
    
    # Сбер
    if content.startswith('https://sberbank.ru/'):
        return content[20:]  # Убираем https://sberbank.ru/
    if content.startswith('https://www.sberbank.ru/'):
        return content[24:]  # Убираем https://www.sberbank.ru/
    
    # ЮMoney
    if content.startswith('https://yoomoney.ru/'):
        return content[20:]  # Убираем https://yoomoney.ru/
    if content.startswith('https://www.yoomoney.ru/'):
        return content[24:]  # Убираем https://www.yoomoney.ru/
    
    # QIWI
    if content.startswith('https://qiwi.com/'):
        return content[17:]  # Убираем https://qiwi.com/
    if content.startswith('https://www.qiwi.com/'):
        return content[21:]  # Убираем https://www.qiwi.com/
    
    # Тинькофф
    if content.startswith('https://tinkoff.ru/'):
        return content[19:]  # Убираем https://tinkoff.ru/
    if content.startswith('https://www.tinkoff.ru/'):
        return content[23:]  # Убираем https://www.tinkoff.ru/
    
    # Kaspi
    if content.startswith('https://kaspi.kz/'):
        return content[17:]  # Убираем https://kaspi.kz/
    if content.startswith('https://www.kaspi.kz/'):
        return content[21:]  # Убираем https://www.kaspi.kz/
    
    # Google Docs
    if content.startswith('https://docs.google.com/'):
        return content[24:]  # Убираем https://docs.google.com/
    
    # Google Sheets
    if content.startswith('https://sheets.google.com/'):
        return content[26:]  # Убираем https://sheets.google.com/
    
    # Google Slides
    if content.startswith('https://slides.google.com/'):
        return content[26:]  # Убираем https://slides.google.com/
    
    # Google Forms
    if content.startswith('https://forms.google.com/'):
        return content[25:]  # Убираем https://forms.google.com/
    
    # Яндекс Диск
    if content.startswith('https://disk.yandex.ru/'):
        return content[23:]  # Убираем https://disk.yandex.ru/
    if content.startswith('https://disk.yandex.com/'):
        return content[23:]  # Убираем https://disk.yandex.com/
    
    # Яндекс Карты
    if content.startswith('https://yandex.ru/maps/'):
        return content[23:]  # Убираем https://yandex.ru/maps/
    if content.startswith('https://yandex.com/maps/'):
        return content[23:]  # Убираем https://yandex.com/maps/
    
    # Google Карты
    if content.startswith('https://maps.google.com/'):
        return content[25:]  # Убираем https://maps.google.com/
    if content.startswith('https://www.google.com/maps/'):
        return content[28:]  # Убираем https://www.google.com/maps/
    
    # 2ГИС
    if content.startswith('https://2gis.ru/'):
        return content[16:]  # Убираем https://2gis.ru/
    if content.startswith('https://2gis.com/'):
        return content[16:]  # Убираем https://2gis.com/
    if content.startswith('https://www.2gis.ru/'):
        return content[20:]  # Убираем https://www.2gis.ru/
    if content.startswith('https://www.2gis.com/'):
        return content[20:]  # Убираем https://www.2gis.com/
    
    # Avito
    if content.startswith('https://avito.ru/'):
        return content[17:]  # Убираем https://avito.ru/
    if content.startswith('https://www.avito.ru/'):
        return content[21:]  # Убираем https://www.avito.ru/
    
    # OLX
    if content.startswith('https://olx.kz/'):
        return content[15:]  # Убираем https://olx.kz/
    if content.startswith('https://www.olx.kz/'):
        return content[19:]  # Убираем https://www.olx.kz/
    
    # DonationAlerts
    if content.startswith('https://donationalerts.com/'):
        return content[27:]  # Убираем https://donationalerts.com/
    if content.startswith('https://www.donationalerts.com/'):
        return content[31:]  # Убираем https://www.donationalerts.com/
    
    # OnlyFans
    if content.startswith('https://onlyfans.com/'):
        return content[21:]  # Убираем https://onlyfans.com/
    if content.startswith('https://www.onlyfans.com/'):
        return content[25:]  # Убираем https://www.onlyfans.com/
    
    # Boosty
    if content.startswith('https://boosty.to/'):
        return content[18:]  # Убираем https://boosty.to/
    if content.startswith('https://www.boosty.to/'):
        return content[22:]  # Убираем https://www.boosty.to/
    
    # Patreon
    if content.startswith('https://patreon.com/'):
        return content[20:]  # Убираем https://patreon.com/
    if content.startswith('https://www.patreon.com/'):
        return content[24:]  # Убираем https://www.patreon.com/
    
    # TeamSpeak
    if content.startswith('ts3server://'):
        return content[12:]  # Убираем ts3server://
    
    # Skype
    if content.startswith('skype:'):
        return content[6:]  # Убираем skype:
    
    # Viber
    if content.startswith('viber://chat?number='):
        return content[20:]  # Убираем viber://chat?number=
    
    # Если это обычная ссылка, возвращаем как есть
    return content


def get_storage_content(content, widget_type, template_id=None):
    """
    Преобразует содержимое виджета в формат для хранения в базе данных
    
    Args:
        content (str): Содержимое из формы
        widget_type (str): Тип виджета
        template_id (str): ID шаблона (опционально)
    
    Returns:
        str: Содержимое для хранения
    """
    if not content:
        return content
    
    # Если уже содержит протокол, возвращаем как есть
    if content.startswith(('http://', 'https://', 'tel:', 'mailto:', 'sms:', 'skype:', 'viber://', 'ts3server://')):
        return content
    
    # Обрабатываем в зависимости от типа виджета и шаблона
    if widget_type == 'contact':
        if 'phone' in (template_id or ''):
            return f"tel:{content.replace('+', '').replace(' ', '')}"
        elif 'email' in (template_id or ''):
            return f"mailto:{content}"
        # Фолбэк без template_id: определяем по содержимому
        normalized = content.strip()
        if '@' in normalized:
            return f"mailto:{normalized}"
        # цифры/+, пробелы, скобки, дефисы
        digits_only = (normalized.replace('+', '')
                                   .replace(' ', '')
                                   .replace('-', '')
                                   .replace('(', '')
                                   .replace(')', ''))
        if digits_only.isdigit():
            return f"tel:{digits_only if normalized.startswith('+') else digits_only}"
    
    elif widget_type == 'social':
        if 'whatsapp' in (template_id or ''):
            return f"https://wa.me/{content.replace('+', '').replace(' ', '')}"
        elif 'telegram' in (template_id or ''):
            return f"https://t.me/{content.replace('@', '')}"
        elif 'instagram' in (template_id or ''):
            return f"https://instagram.com/{content.replace('@', '')}"
        elif 'youtube' in (template_id or ''):
            return f"https://youtube.com/@{content.replace('@', '')}"
        elif 'tiktok' in (template_id or ''):
            return f"https://tiktok.com/@{content.replace('@', '')}"
        elif 'facebook' in (template_id or ''):
            return f"https://facebook.com/{content.replace('@', '')}"
        elif 'linkedin' in (template_id or ''):
            return f"https://linkedin.com/in/{content.replace('@', '')}"
        elif 'twitter' in (template_id or ''):
            return f"https://twitter.com/{content.replace('@', '')}"
        elif 'vk' in (template_id or ''):
            return f"https://vk.com/{content.replace('@', '')}"
        elif 'ok' in (template_id or ''):
            return f"https://ok.ru/{content.replace('@', '')}"
        elif 'snapchat' in (template_id or ''):
            return f"https://snapchat.com/add/{content.replace('@', '')}"
        elif 'pinterest' in (template_id or ''):
            return f"https://pinterest.com/{content.replace('@', '')}"
        elif 'behance' in (template_id or ''):
            return f"https://behance.net/{content.replace('@', '')}"
        elif 'fivehundredpx' in (template_id or ''):
            return f"https://500px.com/{content.replace('@', '')}"
        elif 'twitch' in (template_id or ''):
            return f"https://twitch.tv/{content.replace('@', '')}"
        elif 'discord' in (template_id or ''):
            return f"https://discord.gg/{content.replace('@', '')}"
        elif 'steam' in (template_id or ''):
            return f"https://steamcommunity.com/id/{content.replace('@', '')}"
        elif 'spotify' in (template_id or ''):
            return f"https://open.spotify.com/{content.replace('@', '')}"
        elif 'apple_music' in (template_id or ''):
            return f"https://music.apple.com/{content.replace('@', '')}"
        elif 'soundcloud' in (template_id or ''):
            return f"https://soundcloud.com/{content.replace('@', '')}"
        elif 'yandex_music' in (template_id or ''):
            return f"https://music.yandex.ru/{content.replace('@', '')}"
        elif 'vk_music' in (template_id or ''):
            return f"https://vk.com/audio/{content.replace('@', '')}"
        elif 'boom' in (template_id or ''):
            return f"https://boom.ru/{content.replace('@', '')}"
        elif 'sber_sound' in (template_id or ''):
            return f"https://sber-zvuk.com/{content.replace('@', '')}"
        elif 'youtube_music' in (template_id or ''):
            return f"https://music.youtube.com/{content.replace('@', '')}"
        elif 'yandex_zen' in (template_id or ''):
            return f"https://zen.yandex.ru/{content.replace('@', '')}"
        elif 'kwai' in (template_id or ''):
            return f"https://kwai.com/{content.replace('@', '')}"
        elif 'likee' in (template_id or ''):
            return f"https://likee.video/{content.replace('@', '')}"
        elif 'wechat' in (template_id or ''):
            return f"https://weixin.qq.com/{content.replace('@', '')}"
    
    elif widget_type == 'button':
        if 'sms' in (template_id or ''):
            return f"sms:{content.replace('+', '').replace(' ', '')}"
        elif 'location' in (template_id or ''):
            return f"https://maps.google.com/?q={content}"
    
    elif widget_type == 'link':
        if 'yandex_maps' in (template_id or ''):
            return f"https://yandex.ru/maps/{content}"
        elif 'google_maps' in (template_id or ''):
            return f"https://maps.google.com/?q={content}"
        elif 'two_gis' in (template_id or ''):
            # Преобразуем ссылку 2ГИС в маршрут "как проехать"
            if content.startswith('https://2gis.ru/'):
                # Убираем домен и добавляем параметр маршрута
                path = content.replace('https://2gis.ru/', '').replace('https://www.2gis.ru/', '')
                return f"https://2gis.ru/{path}?m=route"
            elif content.startswith('2gis.ru/'):
                path = content.replace('2gis.ru/', '')
                return f"https://2gis.ru/{path}?m=route"
            else:
                # Если это просто путь, добавляем маршрут
                return f"https://2gis.ru/{content}?m=route"
        # Для обычных ссылок добавляем https:// если нет протокола
        elif not content.startswith(('http://', 'https://')):
            return f"https://{content}"
    
    # Общий фолбэк: если нет схемы и это похоже на email/телефон — нормализуем
    if not content.startswith(('http://', 'https://', 'tel:', 'mailto:', 'sms:', 'skype:', 'viber://', 'ts3server://')):
        raw = content.strip()
        if '@' in raw and ' ' not in raw and '.' in raw.split('@')[-1]:
            return f"mailto:{raw}"
        digits_only = (raw.replace('+', '')
                          .replace(' ', '')
                          .replace('-', '')
                          .replace('(', '')
                          .replace(')', ''))
        if digits_only.isdigit() and len(digits_only) >= 5:
            return f"tel:{digits_only if raw.startswith('+') else digits_only}"

    # Если не подошло ни одно условие, возвращаем как есть
    return content
