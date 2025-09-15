# src/utils/search_functions.py
from typing import Union
import re

def find_key_get_value(key, obj):
    """
    Busca recursivamente una key en un objeto JSON/dict.
    Útil para extraer valores de webhooks complejos.
    """
    if isinstance(obj, dict):
        if key in obj:
            return obj[key]
        for value in obj.values():
            if isinstance(value, (dict, list)):
                result = find_key_get_value(key, value)
                if result is not None:
                    return result

    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                result = find_key_get_value(key, item)
                if result is not None:
                    return result

    return None

def find_channel(channel, channels_array):
    """Verifica si un canal existe en un array de canales"""
    for obj in channels_array:
        if isinstance(obj, dict):
            if any(channel == value for value in obj.values()):
                return True
    return False

def find_mentions(text: str = "", channels_array: list = [], users_trello: list = []):
    """Detecta menciones en texto para Slack y Trello"""
    if len(channels_array) > 0:
        # Busca menciones de Slack: <@U123456>
        channel_ids = [channel["channel_id"] for channel in channels_array]
        for channel_id in channel_ids:
            mention_format = f"<@{channel_id}>"
            if mention_format in text:
                return mention_format

    if len(users_trello) > 0:
        # Busca menciones de Trello: @username
        for user in users_trello:
            if user in text:
                return True

    return None