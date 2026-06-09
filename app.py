import os
import sys
import subprocess
import urllib.request
import urllib.parse
import urllib.error
import zipfile
import json
import base64
import time
try:
	sys.stdout.reconfigure(encoding='utf-8')
	sys.stderr.reconfigure(encoding='utf-8')
except: pass
session = None
cyan = "\033[96m"
green = "\033[92m"
yellow = "\033[93m"
red = "\033[91m"
pink = "\033[95m"
end = "\033[0m"
bold = "\033[1m"
def clear():
	os.system("cls" if sys.platform == "win32" else "clear")
def setup():
	env = sys.platform
	has = False
	try:
		subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		has = True
	except:
		dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ffmpeg")
		if os.path.exists(os.path.join(dir, "ffmpeg.exe")):
			has = True
			os.environ["PATH"] += os.pathsep + dir
	if env == "win32" and not has:
		print(f"{yellow}Installing ffmpeg...{end}")
		try:
			dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "ffmpeg")
			os.makedirs(dir, exist_ok=True)
			src = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
			zip = os.path.join(dir, "ffmpeg.zip")
			urllib.request.urlretrieve(src, zip)
			with zipfile.ZipFile(zip, "r") as z:
				for f in z.namelist():
					if f.endswith(".exe"):
						name = os.path.basename(f)
						file = os.path.join(dir, name)
						with open(file, "wb") as out:
							out.write(z.read(f))
			os.remove(zip)
			subprocess.run(f'setx PATH "%PATH%;{dir}"', shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			os.environ["PATH"] += os.pathsep + dir
			has = True
			print(f"{green}ffmpeg ready!{end}")
		except:
			print(f"{red}ffmpeg failed!{end}")
	elif os.path.exists("/data/data/com.termux") and not has:
		print(f"{yellow}Installing ffmpeg...{end}")
		try:
			subprocess.run(["pkg", "install", "-y", "ffmpeg"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			has = True
			print(f"{green}ffmpeg ready!{end}")
		except:
			print(f"{red}ffmpeg failed!{end}")
	try:
		subprocess.run([sys.executable, "-m", "pip", "install", "-U", "yt-dlp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
	except: pass
	return has
def token():
	global session
	session = urllib.request.build_opener(urllib.request.HTTPCookieProcessor())
	urllib.request.install_opener(session)
	url = "https://spotidown.app/en2"
	headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
	req = urllib.request.Request(url, headers=headers)
	try:
		res = session.open(req, timeout=10)
		html = res.read().decode("utf-8")
		form = html.split('name="spotifyurl"')[1].split('</form>')[0]
		parts = form.split('<input')
		for part in parts[1:]:
			if 'type="hidden"' in part:
				if 'name="g-recaptcha-response"' in part: continue
				name = part.split('name="')[1].split('"')[0]
				val = part.split('value="')[1].split('"')[0]
				return name, val
	except: pass
	return None, None
def tracks(url, key, val):
	global session
	payload = {
		"url": url,
		"g-recaptcha-response": "faketoken",
		key: val
	}
	data = urllib.parse.urlencode(payload).encode()
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Referer": "https://spotidown.app/en2",
		"X-Requested-With": "XMLHttpRequest"
	}
	req = urllib.request.Request("https://spotidown.app/action", data=data, headers=headers)
	try:
		res = session.open(req, timeout=15)
		resp = json.loads(res.read().decode("utf-8"))
		body = resp.get("data", "")
		cover = ""
		if "spotidown-downloader-left" in body:
			cover = body.split("spotidown-downloader-left")[1].split('src="')[1].split('"')[0]
		songs = []
		parts = body.split('<form name="submitspurl"')
		for part in parts[1:]:
			raw = part.split('name="data" value=\'')[1].split('\'')[0]
			parent = part.split('name="base" value="')[1].split('"')[0]
			auth = part.split('name="token" value="')[1].split('"')[0]
			decoded = json.loads(base64.b64decode(raw).decode("utf-8"))
			decoded["raw"] = raw
			decoded["base"] = parent
			decoded["token"] = auth
			songs.append(decoded)
		return songs, cover
	except: pass
	return [], ""
def link(song):
	global session
	payload = {
		"data": song.get("raw", ""),
		"base": song.get("base", ""),
		"token": song.get("token", "")
	}
	data = urllib.parse.urlencode(payload).encode()
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Referer": "https://spotidown.app/en2",
		"X-Requested-With": "XMLHttpRequest"
	}
	req = urllib.request.Request("https://spotidown.app/action/track", data=data, headers=headers)
	try:
		res = session.open(req, timeout=15)
		resp = json.loads(res.read().decode("utf-8"))
		html = resp.get("data", "")
		href = html.split('id="popup" href="')[1].split('"')[0]
		return href
	except: pass
	return None
def retrieve(url, path):
	global session
	headers = {
		"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
		"Referer": "https://spotidown.app/"
	}
	req = urllib.request.Request(url, headers=headers)
	try:
		res = session.open(req, timeout=30)
		with open(path, "wb") as out:
			out.write(res.read())
		return True
	except: pass
	return False
def clean(text):
	for c in ['\\', '/', ':', '*', '?', '"', '<', '>', '|']:
		text = text.replace(c, "")
	return text.strip()
def save(song, opt, has, br, path=None):
	title = song.get("name", "")
	arts = song.get("artist", "")
	query = f"{title} {arts}".strip()
	out = path
	if not out:
		out = clean(f"{title} - {arts}") + (".mp3" if opt == "1" else ".mp4")
	ok = False
	if opt == "1":
		lnk = link(song)
		if lnk:
			print(f"{yellow}Downloading MP3...{end}")
			ok = retrieve(lnk, out)
			if ok:
				print(f"\a{green}{bold}[v] Success!{end}")
			else:
				print(f"\a{red}{bold}[x] Failed!{end}")
			if ok and not path:
				cover = song.get("cover", "")
				if cover:
					try:
						urllib.request.urlretrieve(cover, "temp.jpg")
						subprocess.run(["ffmpeg", "-y", "-i", out, "-i", "temp.jpg", "-c", "copy", "-map", "0", "-map", "1", "-id3v2_version", "3", "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (Front)", "tagged.mp3"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
						if os.path.exists("tagged.mp3") and os.path.getsize("tagged.mp3") > 0:
							os.remove(out)
							os.rename("tagged.mp3", out)
					except: pass
					finally:
						if os.path.exists("temp.jpg"):
							try: os.remove("temp.jpg")
							except: pass
	if not ok:
		ok = download("ytsearch:" + query, opt, has, br, path=out)
	return ok
def fetch(url, full=False):
	try:
		src = f"https://open.spotify.com/oembed?url={url}"
		req = urllib.request.Request(src, headers={"User-Agent": "Mozilla/5.0"})
		res = urllib.request.urlopen(req, timeout=8)
		data = json.loads(res.read().decode("utf-8"))
		title = data.get("title", "")
		if full: return title or None
		name = data.get("author_name", "")
		if title: return f"ytsearch:{title} {name}".strip()
	except: pass
	return None
def wipe(keep=False):
	if not os.path.exists("temp"): return
	for f in os.listdir("temp"):
		if keep and not (f.endswith(".part") or f.endswith(".ytdl")): continue
		try: os.remove(os.path.join("temp", f))
		except: pass
def join(opt):
	dir = "temp"
	txt = "list.txt"
	out = "playlist.mp3" if opt == "1" else "playlist.mp4"
	ext = ".mp3" if opt == "1" else ".mp4"
	try:
		files = sorted([f for f in os.listdir(dir) if f.endswith(ext) and not f.startswith("silence") and os.path.getsize(os.path.join(dir, f)) > 0], key=lambda x: int(x.split(".")[0]) if x.split(".")[0].isdigit() else 0)
		if not files: return False
		ok = False
		silence = os.path.join(dir, "silence" + ext)
		if opt == "1":
			subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1", "-c:a", "libmp3lame", silence], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		else:
			subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "color=c=black:s=1280x720:d=1", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo", "-t", "1", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", silence], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		seq = []
		for idx, f in enumerate(files):
			if idx > 0:
				seq.append("silence" + ext)
			seq.append(f)
		args = ["ffmpeg", "-y"]
		for f in seq:
			args.extend(["-i", os.path.join(dir, f)])
		parts = []
		inputs = []
		for idx in range(len(seq)):
			if opt == "1":
				parts.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo[a{idx}]")
				inputs.append(f"[a{idx}]")
			else:
				parts.append(f"[{idx}:v]scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1[v{idx}]")
				parts.append(f"[{idx}:a]aresample=44100,aformat=channel_layouts=stereo[a{idx}]")
				inputs.append(f"[v{idx}][a{idx}]")
		graph = ";".join(parts)
		if graph:
			graph += ";"
		if opt == "1":
			graph += f"{''.join(inputs)} concat=n={len(seq)}:v=0:a=1 [a]"
		else:
			graph += f"{''.join(inputs)} concat=n={len(seq)}:v=1:a=1 [v][a]"
		script = "filter.txt"
		try:
			with open(script, "w", encoding="utf-8") as f:
				f.write(graph)
		except: return False
		if opt == "1":
			args.extend(["-filter_complex_script", script, "-map", "[a]", "-c:a", "libmp3lame", "-b:a", "192k", out])
		else:
			args.extend(["-filter_complex_script", script, "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "ultrafast", "-c:a", "aac", "-b:a", "128k", out])
		res = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
		ok = res.returncode == 0 and os.path.exists(out) and os.path.getsize(out) > 0
		try: os.remove(script)
		except: pass
		try: os.remove(silence)
		except: pass
		if ok:
			cover = os.path.join(dir, "cover.jpg")
			if os.path.exists(cover):
				try:
					if opt == "1":
						args = ["ffmpeg", "-y", "-i", out, "-i", cover, "-c", "copy", "-map", "0", "-map", "1", "-id3v2_version", "3", "-metadata:s:v", "title=Album cover", "-metadata:s:v", "comment=Cover (Front)", "merged.mp3"]
						res = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
						if res.returncode == 0 and os.path.exists("merged.mp3") and os.path.getsize("merged.mp3") > 0:
							os.remove(out)
							os.rename("merged.mp3", out)
						else:
							if os.path.exists("merged.mp3"):
								try: os.remove("merged.mp3")
								except: pass
					else:
						args = ["ffmpeg", "-y", "-i", out, "-i", cover, "-map", "0", "-map", "1", "-c", "copy", "-disposition:v:1", "attached_pic", "merged.mp4"]
						res = subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
						if res.returncode == 0 and os.path.exists("merged.mp4") and os.path.getsize("merged.mp4") > 0:
							os.remove(out)
							os.rename("merged.mp4", out)
						else:
							if os.path.exists("merged.mp4"):
								try: os.remove("merged.mp4")
								except: pass
				except: pass
			for f in os.listdir(dir):
				try: os.remove(os.path.join(dir, f))
				except: pass
			try: os.rmdir(dir)
			except: pass
			return True
		return False
	except: return False
def count(url):
	try:
		args = [sys.executable, "-m", "yt_dlp", "--flat-playlist", "--print", "playlist_count", url]
		res = subprocess.run(args, capture_output=True, text=True)
		if res.returncode == 0:
			lines = res.stdout.strip().split("\n")
			for l in lines:
				if l.strip().isdigit():
					return int(l.strip())
	except: pass
	return 0
def scan(ext):
	if not os.path.exists("temp"): return 0
	try:
		files = sorted([f for f in os.listdir("temp") if f.endswith(ext) and os.path.getsize(os.path.join("temp", f)) > 0])
		seq = set()
		for f in files:
			name = f.split(".")[0]
			if name.isdigit(): seq.add(int(name))
		if not seq: return 0
		m = max(seq)
		for i in range(1, m + 1):
			if i not in seq: return i - 1
		return m
	except: return 0
def browsers():
	mobile = os.path.exists("/data/data/com.termux") or os.path.exists("/proc/ish")
	if mobile: return []
	home = os.path.expanduser("~")
	if sys.platform == "win32":
		loc = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
		ap = os.environ.get("APPDATA", os.path.join(home, "AppData", "Roaming"))
		map = {"chrome": os.path.join(loc, "Google", "Chrome", "User Data"), "edge": os.path.join(loc, "Microsoft", "Edge", "User Data"), "firefox": os.path.join(ap, "Mozilla", "Firefox", "Profiles")}
	elif sys.platform == "darwin":
		map = {"chrome": os.path.join(home, "Library", "Application Support", "Google", "Chrome"), "firefox": os.path.join(home, "Library", "Application Support", "Firefox", "Profiles"), "safari": os.path.join(home, "Library", "Safari")}
	else:
		map = {"chrome": os.path.join(home, ".config", "google-chrome"), "firefox": os.path.join(home, ".mozilla", "firefox")}
	found = []
	for name, path in map.items():
		if os.path.exists(path):
			found.append(name)
	try:
		if sys.platform == "win32":
			task = subprocess.run(["tasklist"], capture_output=True, text=True)
			out = task.stdout.lower()
			active = {"chrome": "chrome.exe" in out, "edge": "msedge.exe" in out, "firefox": "firefox.exe" in out}
		else:
			task = subprocess.run(["ps", "-ax"], capture_output=True, text=True)
			out = task.stdout.lower()
			active = {"chrome": "chrome" in out, "edge": "edge" in out, "firefox": "firefox" in out, "safari": "safari" in out}
		for name, running in active.items():
			if running and name in found:
				found.remove(name)
				found.append(name)
	except: pass
	return found
def download(url, opt, has, br, path=None):
	single = url.endswith("&single")
	if single: url = url[:-7]
	play = ("list=" in url or "/playlist" in url or "/album" in url or "/sets/" in url or "/mix/" in url or "bilibili.com" in url and ("?p=" in url or "multi" in url)) and not single
	args = [sys.executable, "-m", "yt_dlp", "--no-warnings"]
	if has and ("youtube.com" in url or "youtu.be" in url or url.startswith("ytsearch:")):
		args.extend(["--embed-metadata", "--sponsorblock-remove", "music_offtopic"])
		if not play and not path:
			args.append("--embed-thumbnail")
	if play and not has:
		print(f"{red}[x] Need ffmpeg!{end}")
		return False
	if play:
		num = count(url)
		limit = 0
		if num > 60:
			print(f"{yellow}[!] {num} tracks!{end}")
			ans = input(f"{cyan}Limit (Enter for all): {end}").strip()
			if ans.isdigit():
				limit = int(ans)
		num = limit if limit > 0 else num
		print(f"{yellow}[!] {num} tracks.{end}")
		ext = ".mp3" if opt == "1" else ".mp4"
		start = 1
		old = ""
		if os.path.exists(os.path.join("temp", "url.txt")):
			try:
				with open(os.path.join("temp", "url.txt"), "r", encoding="utf-8") as f:
					old = f.read().strip()
			except: pass
		if old == url:
			idx = scan(ext)
			if idx > 0:
				print(f"{yellow}[i] Found 1-{idx}.{end}")
				ans = input(f"{cyan}Resume from {idx + 1}? (y/n): {end}").strip().lower()
				if ans == "y":
					start = idx + 1
					wipe(keep=True)
				else:
					wipe()
			else:
				os.makedirs("temp", exist_ok=True)
		else:
			wipe()
			os.makedirs("temp", exist_ok=True)
		try:
			with open(os.path.join("temp", "url.txt"), "w", encoding="utf-8") as f:
				f.write(url)
		except: pass
		try:
			subprocess.run([sys.executable, "-m", "yt_dlp", "--playlist-items", "1", "--write-thumbnail", "--skip-download", "-o", "temp/cover", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			for x in [".webp", ".png", ".jpg"]:
				f = os.path.join("temp", "cover" + x)
				if os.path.exists(f):
					if x != ".jpg":
						subprocess.run(["ffmpeg", "-y", "-i", f, os.path.join("temp", "cover.jpg")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
						os.remove(f)
					else:
						os.rename(f, os.path.join("temp", "cover.jpg"))
					break
		except: pass
		if limit > 0 and start > limit:
			print(f"{green}[v] Done!{end}")
			return True
		args.append("--yes-playlist")
		if start > 1:
			args.extend(["--playlist-start", str(start)])
		if limit > 0:
			args.extend(["--playlist-end", str(limit)])
		if opt == "1":
			args.extend(["-f", "bestaudio", "--extract-audio", "--audio-format", "mp3", "-o", "temp/%(playlist_index)03d.%(ext)s", url])
			print(f"{yellow}Downloading MP3...{end}")
		else:
			args.extend(["-f", "best[height<=720][ext=mp4]/best[ext=mp4]/best", "--recode-video", "mp4", "-o", "temp/%(playlist_index)03d.%(ext)s", url])
			print(f"{yellow}Downloading MP4...{end}")
	else:
		args.append("--no-playlist")
		if opt == "1":
			if has:
				args.extend(["-f", "bestaudio", "--extract-audio", "--audio-format", "mp3"])
				if not path:
					print(f"{yellow}Downloading MP3...{end}")
			else:
				args.extend(["-f", "bestaudio[ext=m4a]/bestaudio"])
				if not path:
					print(f"{yellow}Downloading M4A...{end}")
		else:
			if has:
				args.extend(["-f", "bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/best", "--merge-output-format", "mp4"])
				if not path:
					print(f"{yellow}Downloading MP4...{end}")
			else:
				args.extend(["-f", "best[ext=mp4]/best"])
				if not path:
					print(f"{yellow}Downloading MP4...{end}")
		if path:
			args.extend(["-o", path])
		args.append(url)
	try:
		ok = False
		if br:
			for b in br:
				temp = args + ["--cookies-from-browser", b]
				res = subprocess.run(temp, stderr=subprocess.DEVNULL)
				if res.returncode == 0:
					ok = True
					break
			if not ok:
				res = subprocess.run(args, stderr=subprocess.DEVNULL if path else None)
				ok = (res.returncode == 0)
		else:
			res = subprocess.run(args, stderr=subprocess.DEVNULL if path else None)
			ok = (res.returncode == 0)
		if play:
			if ok:
				print(f"{yellow}Merging...{end}")
				if join(opt):
					print(f"\a{green}{bold}[v] Merged!{end}")
					return True
				else:
					print(f"\a{red}{bold}[x] Failed!{end}")
					return False
			else:
				print(f"{red}[!] Download failed!{end}")
				ans = input(f"{cyan}Merge anyway? (y/n): {end}").strip().lower()
				if ans == "y":
					print(f"{yellow}Merging...{end}")
					if join(opt):
						print(f"\a{green}{bold}[v] Merged!{end}")
						return True
					else:
						print(f"\a{red}{bold}[x] Failed!{end}")
						return False
				else:
					print(f"{yellow}[i] Kept temp. Run again to resume.{end}")
					return False
		else:
			if ok:
				print(f"\a{green}{bold}[v] Success!{end}")
				return True
			else:
				print(f"\a{red}{bold}[x] Failed!{end}")
				return False
	except KeyboardInterrupt:
		raise
	except:
		print(f"\a{red}{bold}[x] Error!{end}")
		return False
def run():
	has = setup()
	clear()
	br = browsers()
	try:
		while True:
			raw = input(f"{pink}[>] Link: {end}").strip()
			if not raw:
				print(f"{red}[x] Empty!{end}")
				continue
			url = "".join(c for c in raw if 32 <= ord(c) <= 126).strip()
			if not url:
				print(f"{red}[x] Empty!{end}")
				continue
			if not url.startswith("http://") and not url.startswith("https://") and not url.startswith("ytsearch:"):
				url = "ytsearch:" + raw
			if "spotify.com" in url:
				if "?" in url: url = url.split("?")[0]
				name, val = token()
				songs, cover = tracks(url, name, val) if name else ([], "")
				if not songs:
					name = fetch(url, full=True)
					print(f"{red}[x] Spotify error!{end}" if not name else f"{red}[x] {name}: no tracks!{end}")
					continue
				play = "/playlist" in url or "/album" in url
				if play:
					num = len(songs)
					limit = 0
					if num > 60:
						print(f"{yellow}[!] {num} tracks!{end}")
						ans = input(f"{cyan}Limit (Enter for all): {end}").strip()
						if ans.isdigit():
							limit = int(ans)
					if limit > 0:
						songs = songs[:limit]
					print(f"{yellow}[!] {len(songs)} tracks.{end}")
					opt = input(f"{cyan}[*] Format (1. MP3 | 2. MP4): {end}").strip()
					if opt not in ["1", "2"]:
						print(f"{red}[x] Invalid!{end}")
						continue
					clear()
					wipe()
					os.makedirs("temp", exist_ok=True)
					if cover:
						try: urllib.request.urlretrieve(cover, os.path.join("temp", "cover.jpg"))
						except: pass
					for idx, song in enumerate(songs):
						title = song.get("name", "")
						arts = song.get("artist", "")
						query = f"{title} {arts}".strip()
						print(f"{cyan}[{idx+1}/{len(songs)}] {query}{end}")
						dest = os.path.join("temp", f"{idx+1:03d}.mp3" if opt == "1" else f"{idx+1:03d}.mp4")
						save(song, opt, has, br, path=dest)
					print(f"{yellow}Merging...{end}")
					if join(opt): print(f"\a{green}{bold}[v] Merged!{end}")
					else: print(f"\a{red}{bold}[x] Failed!{end}")
				else:
					song = songs[0]
					title = song.get("name", "")
					arts = song.get("artist", "")
					query = f"{title} {arts}".strip()
					print(f"{cyan}[1/1] {query}{end}")
					opt = input(f"{cyan}[*] Format (1. MP3 | 2. MP4): {end}").strip()
					if opt not in ["1", "2"]:
						print(f"{red}[x] Invalid!{end}")
						continue
					clear()
					save(song, opt, has, br)
				again = input(f"{cyan}[?] Again? (y/n): {end}").strip().lower()
				if again != "y":
					print(f"{green}Bye!{end}")
					break
				clear()
				continue
			elif "list=" in url:
				lst = url.split("list=")[1].split("&")[0]
				if lst.startswith("RD") and len(lst) == 13:
					vid = lst[2:]
					url = f"https://www.youtube.com/watch?v={vid}&list={lst}"
				else:
					if "youtube.com/watch" in url or "youtu.be/" in url:
						ans = input(f"{cyan}1. Playlist | 2. Video: {end}").strip()
						if ans == "1":
							url = "https://www.youtube.com/playlist?list=" + lst
						else:
							if "?" in url:
								base, query = url.split("?", 1)
								parts = [p for p in query.split("&") if not p.startswith("list=")]
								url = base + ("?" + "&".join(parts) if parts else "")
							url += "&single"
					else:
						url = "https://www.youtube.com/playlist?list=" + lst
			elif "bilibili.com" in url and ("?p=" in url or "multi" in url):
				ans = input(f"{cyan}1. Playlist | 2. Video: {end}").strip()
				if ans != "1": url += "&single"
			elif "/playlist" in url or "/album" in url or "/sets/" in url or "/mix/" in url:
				pass
			else:
				if "youtube.com/watch" in url or "youtu.be/" in url:
					if "&" in url: url = url.split("&")[0]
				elif "bilibili.com" in url: pass
				elif "?" in url: url = url.split("?")[0]
			opt = input(f"{cyan}[*] Format (1. MP3 | 2. MP4): {end}").strip()
			if opt not in ["1", "2"]:
				print(f"{red}[x] Invalid!{end}")
				continue
			clear()
			download(url, opt, has, br)
			again = input(f"{cyan}[?] Again? (y/n): {end}").strip().lower()
			if again != "y":
				print(f"{green}Bye!{end}")
				break
			clear()
	except KeyboardInterrupt:
		print(f"\n{red}[!] Interrupted!{end}")
		os._exit(1)
if __name__ == "__main__":
	run()
