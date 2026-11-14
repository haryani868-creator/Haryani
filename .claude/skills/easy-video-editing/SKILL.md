---
name: easy-video-editing
description: Simple video editing for reels and social media with ffmpeg, faster-whisper and OpenCV. Use when the person uploads a video and asks to transcribe it ("write down what they say"), add captions or pop-up captions, make it vertical / follow the face, cut silent parts, trim, join clips, add background music, speed up, make it smaller for WhatsApp, or make a cover photo. Handles English and Malay.
---

# Easy Video Editing

The person is a beginner. Talk in plain, simple words. Don't show commands unless they ask.

Scripts live next to this file in `scripts/` (call them as `python3 <skill-dir>/scripts/NAME.py`,
where `<skill-dir>` is the folder holding this SKILL.md, normally `.claude/skills/easy-video-editing`).

## 0. Make sure the tools are installed (each new cloud session)

```bash
PIP="pip install --break-system-packages -q"
command -v ffmpeg >/dev/null || { apt-get update -q && apt-get install -y -q ffmpeg; }
fc-list | grep -qi montserrat || { apt-get update -q >/dev/null; apt-get install -y -q fonts-montserrat >/dev/null 2>&1 || true; }
python3 -c "import faster_whisper, cv2" 2>/dev/null || $PIP faster-whisper "av<19" "opencv-contrib-python-headless<5" numpy
```

Speech-to-text also needs the Whisper model from Hugging Face. If downloading it fails with
`403 Forbidden` / `ProxyError`, the Hugging Face domains are not allowed in the cloud environment.
Tell the person in one line, and offer to add these hosts to the environment (needs their approval):
`huggingface.co`, `cdn-lfs.hf.co`, `cas-bridge.xethub.hf.co`, `cas-server.xethub.hf.co`.
Everything except transcribe/captions still works without it.

## 1. Where files are

Uploads arrive in `~/.claude/uploads/<id>/` (older setups: `/mnt/user-data/uploads/`).
Find them with `ls -t ~/.claude/uploads/*/ /mnt/user-data/uploads/ 2>/dev/null`.
Never change the original. Copy it, and write results into the project folder with clear names
(e.g. `reel-captions.mp4`) so the person can open them.

## 2. Check your work after every edit

- Length/size: `ffprobe -v error -show_entries format=duration:stream=width,height -of csv=p=0 out.mp4`
- Contact sheet across the whole video (look at it):
  `ffmpeg -i out.mp4 -vf "fps=6/DUR,scale=270:-1,tile=6x1" -frames:v 1 sheet.jpg` (DUR = length in seconds)
- Reels: 1080x1920 (9:16), H.264 + AAC, `-pix_fmt yuv420p`, `-movflags +faststart`.

## 3. Recipes

**Transcribe** -> `in.srt` + `in_words.json`
```bash
python3 scripts/transcribe.py in.mp4 --lang en
python3 scripts/transcribe.py in.mp4 --lang ms --model medium --prompt "names, brand words"   # Malay
```
Show the person the text. Fix wrong names in the .srt by hand.

**Pop-up captions burned in** (video must already be 1080x1920)
```bash
python3 scripts/popcaps.py in.srt caps.ass --accent "FREE,WEIGHT"
ffmpeg -i in.mp4 -vf "ass=caps.ass" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart out.mp4
```

**Plain captions burned in**
```bash
ffmpeg -i in.mp4 -vf "subtitles=in.srt:force_style='FontName=Montserrat,FontSize=14,Bold=1,Outline=2,MarginV=60'" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart out.mp4
```

**Vertical, following the face** (about 3 s of work per 1 s of video)
```bash
python3 scripts/facetrack.py in.mp4 out.mp4      # calmer: --smooth 0.04, faster: --every 5
```
With two people it follows the biggest face. No face found -> keeps the centre.

**Cut pauses**
```bash
python3 scripts/cutpauses.py in.mp4 out.mp4 --min 0.35
```

**Trim** (keep 0:05 to 0:20)
```bash
ffmpeg -ss 00:00:05 -to 00:00:20 -i in.mp4 -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart out.mp4
```

**Join clips** (re-encodes, so clips from different phones still join)
```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];[1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart out.mp4
```
More clips: add inputs and `[v2][2:a]`, set `n=`. A clip with no sound needs a silent track first
(`-f lavfi -t LEN -i anullsrc=r=48000:cl=stereo`, then use that input's audio).

**9:16 with blurred background**
```bash
ffmpeg -i in.mp4 -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];[0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a copy -movflags +faststart out.mp4
```

**Music under the voice** (music ~15%, fades out at the end; `normalize=0` keeps the voice at full volume)
```bash
ffmpeg -i in.mp4 -stream_loop -1 -i music.mp3 -filter_complex "[1:a]volume=0.15,atrim=0:DUR,afade=t=out:st=DUR-2:d=2[m];[0:a][m]amix=inputs=2:duration=first:normalize=0[a]" -map 0:v -map "[a]" -c:v copy -c:a aac -movflags +faststart out.mp4
```
Replace DUR with the video length from ffprobe. Only music the person owns or that is royalty-free.
Never put song lyrics on screen.

**Speed up 1.2x**
```bash
ffmpeg -i in.mp4 -filter_complex "[0:v]setpts=PTS/1.2[v];[0:a]atempo=1.2[a]" -map "[v]" -map "[a]" -c:v libx264 -crf 18 -pix_fmt yuv420p -c:a aac -movflags +faststart out.mp4
```

**Smaller for WhatsApp** (long side 1280, never upscales, works for vertical and landscape)
```bash
ffmpeg -i in.mp4 -vf "scale='if(gt(iw,ih),min(1280,iw),-2)':'if(gt(iw,ih),-2,min(1280,ih))'" -c:v libx264 -crf 28 -preset slow -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart small.mp4
```

**Cover photo**
```bash
ffmpeg -ss 00:00:03 -i in.mp4 -frames:v 1 -q:v 2 cover.jpg
```

## Rules
- Plain words with the person. Keep the original untouched. Clear output names.
- Captions sit in the lower middle so TikTok/Instagram buttons don't cover them.
- If something fails, say what failed in one line and try the next simplest way.
- Always remind them to watch the video before posting.
