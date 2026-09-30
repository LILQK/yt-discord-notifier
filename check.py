import os, json, urllib.request, xml.etree.ElementTree as ET

WEBHOOK = os.environ["DISCORD_WEBHOOK"]
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def send(content):
    req = urllib.request.Request(WEBHOOK, json.dumps({"content": content}).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "yt-notifier"})
    urllib.request.urlopen(req)


def check(state_file, item_id, message):
    last = open(state_file).read().strip() if os.path.exists(state_file) else ""
    if item_id == last:
        print(state_file, "nada nuevo")
        return
    if last:  # la primera ejecución solo guarda el estado, no avisa
        send(message)
    open(state_file, "w").write(item_id)
    print(state_file, "nuevo:", item_id)


def youtube():
    channel = os.environ["YT_CHANNEL_ID"]
    feed = urllib.request.urlopen(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel}").read()
    entry = ET.fromstring(feed).find("a:entry", NS)
    if entry is None:
        return
    vid = entry.find("yt:videoId", NS).text
    title = entry.find("a:title", NS).text
    check("last_video.txt", vid, f"📢 **New video!** {title}\nhttps://youtu.be/{vid}")


def patreon_get(url):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {os.environ['PATREON_TOKEN']}",
                                               "User-Agent": "yt-notifier"})
    return json.load(urllib.request.urlopen(req))


def patreon():
    if not os.environ.get("PATREON_TOKEN"):
        print("Patreon: sin token, se omite")
        return
    api = "https://www.patreon.com/api/oauth2/v2"
    campaign = patreon_get(f"{api}/campaigns")["data"][0]["id"]
    url = f"{api}/campaigns/{campaign}/posts?fields%5Bpost%5D=title,url,published_at&page%5Bcount%5D=100"
    posts = []
    while url:
        page = patreon_get(url)
        posts += [p for p in page["data"] if p["attributes"].get("published_at")]
        url = page.get("links", {}).get("next")
    if not posts:
        return
    post = max(posts, key=lambda p: p["attributes"]["published_at"])
    a = post["attributes"]
    link = a["url"] if a["url"].startswith("http") else "https://www.patreon.com" + a["url"]
    check("last_patreon.txt", post["id"], f"🎉 **New Patreon post!** {a['title']}\n{link}")


errors = []
for fn in (youtube, patreon):
    try:
        fn()
    except Exception as e:  # que un fallo en uno no bloquee al otro
        print(fn.__name__, "ERROR:", e)
        errors.append(fn.__name__)
if errors:
    raise SystemExit(f"Fallaron: {errors}")
