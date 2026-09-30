import os, json, urllib.request, xml.etree.ElementTree as ET

CHANNEL_ID = os.environ["YT_CHANNEL_ID"]
WEBHOOK = os.environ["DISCORD_WEBHOOK"]
STATE = "last_video.txt"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}

feed = urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}").read()
entry = ET.fromstring(feed).find("a:entry", NS)
if entry is None:
    raise SystemExit("Sin vídeos")

vid = entry.find("yt:videoId", NS).text
title = entry.find("a:title", NS).text
last = open(STATE).read().strip() if os.path.exists(STATE) else ""

if vid != last:
    if last:  # la primera ejecución solo guarda el estado, no avisa
        msg = {"content": f"📢 **¡Nuevo vídeo!** {title}\nhttps://youtu.be/{vid}"}
        req = urllib.request.Request(WEBHOOK, json.dumps(msg).encode(),
                                     {"Content-Type": "application/json", "User-Agent": "yt-notifier"})
        urllib.request.urlopen(req)
    open(STATE, "w").write(vid)
    print("Nuevo:", vid)
else:
    print("Nada nuevo")
