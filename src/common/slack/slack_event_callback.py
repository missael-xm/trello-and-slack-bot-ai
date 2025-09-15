# src/common/slack/slack_event_callback.py
from utils.search_functions import find_channel, find_key_get_value, find_mentions
from utils.slack import channels

def event_callback(response):
    """Callback para eventos de Slack (actualmente en desarrollo)"""
    value_of_key = find_key_get_value("channel_type", response)

    if value_of_key == "im":
        print("filter by direct message: ", value_of_key)
        return "Match"
    else:
        value_of_key = find_key_get_value("channel", response)
        if value_of_key is not None:
            channel_found = find_channel(value_of_key, channels)
            if channel_found:
                mention_found = find_mentions(
                    text=find_key_get_value("text", response),
                    channels_array=channels
                )
                if mention_found is not None:
                    print("filter by mention: ", mention_found)
                    return "Match"
    return "No matches"