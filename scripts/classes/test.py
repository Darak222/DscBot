import json
with open('motives.json', 'r', encoding='utf8') as f:
    channel_dict = json.load(f)

    i = 0
    for channels in channel_dict.values():
        print(i)
        print(channels['text_channels'])
        i += 1


