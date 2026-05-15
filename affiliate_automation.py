#!/usr/bin/env python3
"""Full automation toolkit affiliate (Bahasa Indonesia).

Mencakup:
- Riset keyword trending otomatis (Google Trends Indonesia)
- Pembuatan konten (hook, script video, caption, hashtag, komentar)
- Pembuatan backsound sederhana otomatis (tone WAV) jika belum ada
- Pembuatan aset video (jika ffmpeg ada) / placeholder (jika tidak)
- Penjadwalan + antrian auto-post multi-platform
- Eksekusi auto-post via webhook generik (bisa dihubungkan ke Zapier/Make/n8n/API internal)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import shutil
import struct
import subprocess
import urllib.request
import wave
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from textwrap import fill

SUPPORTED_AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg"}
DEFAULT_TRENDS_ID = ["diskon shopee", "viral tiktok", "flash sale", "racun shopee", "produk estetik"]
TRACKER_HEADERS = [
    "date", "platform", "product", "price_usd", "estimated_commission_usd", "hook", "link", "posted_at", "clicks", "orders", "earnings_usd"
]

HOOK_TEMPLATES_ID = [
    "{trend} lagi naik. {product} bantu {problem} lebih cepat.",
    "Aku baru pakai {product}, kenapa nggak dari dulu?",
    "{product} harga ${price}, kepakai tiap hari.",
    "Solusi hemat untuk {problem}: {product}.",
]

CAPTION_TEMPLATES_ID = [
    "Lagi rame: {trend}. {product} cocok buat {problem}. 🎯 Link di bio. 🎵 {backsound}",
    "Budget ${price}, hasil maksimal. {product}. Backsound: {backsound}. 🔥",
    "Daily find: {product}. Lagi trend: {trend}. Cek link affiliate ya. 🎵 {backsound}",
]

COMMENT_REPLIES_ID = [
    "Link ada di bio ya, produk paling atas ✅",
    "Untuk Facebook Group juga sudah aku jadwalkan, cek posting terbaru 👀",
    "Kalau mau harga terbaik, ambil saat flash sale 🔥",
]


@dataclass
class Product:
    name: str
    price: float
    problem: str


def get_trending_keywords_id(limit: int = 10) -> list[str]:
    url = "https://trends.google.com/trending/rss?geo=ID"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            data = r.read()
        root = ET.fromstring(data)
        keywords = [n.text.strip() for n in root.findall("./channel/item/title") if n.text and n.text.strip()]
        return (keywords or DEFAULT_TRENDS_ID)[:limit]
    except Exception:
        return DEFAULT_TRENDS_ID[:limit]


def render_list(template_list: list[str], total: int, **kwargs: str) -> list[str]:
    out = []
    i = 0
    while len(out) < total:
        out.append(template_list[i % len(template_list)].format(**kwargs))
        i += 1
    return out


def write_bullets(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(f"- {x}" for x in lines) + "\n", encoding="utf-8")


def create_tracker(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(TRACKER_HEADERS)


def create_schedule(path: Path, start: datetime, posts: int, step_minutes: int) -> list[datetime]:
    slots, rows = [], ["time_utc,slot,action"]
    for i in range(posts):
        t = start + timedelta(minutes=step_minutes * i)
        slots.append(t)
        rows.append(f"{t.isoformat(timespec='minutes')},{i+1},Posting otomatis")
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return slots


def generate_backsound_library(audio_dir: Path, amount: int = 3, duration_sec: int = 6, sample_rate: int = 44100) -> list[Path]:
    audio_dir.mkdir(parents=True, exist_ok=True)
    frequencies = [220, 330, 440, 550, 660]
    created = []
    for i in range(amount):
        freq = frequencies[i % len(frequencies)]
        out = audio_dir / f"backsound_auto_{i+1:02d}.wav"
        with wave.open(str(out), "w") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            for n in range(sample_rate * duration_sec):
                val = int(32767 * 0.2 * math.sin(2 * math.pi * freq * n / sample_rate))
                w.writeframes(struct.pack("<h", val))
        created.append(out)
    return created


def choose_backsounds(audio_dir: Path, count: int, auto_generate: bool = True) -> list[Path]:
    files = [p for p in audio_dir.glob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXT]
    if not files and auto_generate:
        files = generate_backsound_library(audio_dir, amount=max(3, min(count, 8)))
    if not files:
        raise ValueError("Backsound kosong dan auto-generate dimatikan.")
    if count <= len(files):
        return random.sample(files, count)
    return [files[i % len(files)] for i in range(count)]


def wrap_text_draw(text: str, width: int = 24) -> str:
    return "\\n".join(fill(text, width=width).splitlines()).replace(":", "\\:").replace("'", "\\'")


def run_ffmpeg(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def create_videos(video_dir: Path, hooks: list[str], backsounds: list[Path], duration: int) -> list[Path]:
    video_dir.mkdir(parents=True, exist_ok=True)
    outs = []
    ffmpeg_ok = shutil.which("ffmpeg") is not None
    for i, hook in enumerate(hooks, start=1):
        if ffmpeg_ok:
            out = video_dir / f"short_{i:02d}.mp4"
            cmd = [
                "ffmpeg", "-y", "-f", "lavfi", "-i", f"color=c=0x111111:s=1080x1920:d={duration}",
                "-stream_loop", "-1", "-i", str(backsounds[(i - 1) % len(backsounds)]),
                "-vf", f"drawtext=fontcolor=white:fontsize=56:x=(w-text_w)/2:y=(h-text_h)/2:text='{wrap_text_draw(hook)}'",
                "-t", str(duration), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(out),
            ]
            run_ffmpeg(cmd)
        else:
            out = video_dir / f"short_{i:02d}.txt"
            out.write_text(f"FFmpeg tidak ada.\nHook: {hook}\nBacksound: {backsounds[(i - 1) % len(backsounds)].name}\n", encoding="utf-8")
        outs.append(out)
    return outs


def build_content_plan(path: Path, hooks: list[str], captions: list[str], trends: list[str]) -> None:
    rows = ["slot,trend,hook,caption"]
    n = max(len(hooks), len(captions))
    for i in range(n):
        rows.append(f'{i+1},"{trends[i % len(trends)]}","{hooks[i % len(hooks)]}","{captions[i % len(captions)]}"')
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def build_autopost_queue(path: Path, slots: list[datetime], videos: list[Path], captions: list[str], platforms: list[str]) -> dict:
    posts = []
    for i, dt in enumerate(slots):
        posts.append({
            "slot": i + 1,
            "publish_at_utc": dt.isoformat(),
            "video_path": str(videos[i % len(videos)]),
            "caption": captions[i % len(captions)],
            "platforms": platforms,
            "targets": {
                "facebook_page": True,
                "facebook_group": True,
                "tiktok": True,
                "instagram": True,
            },
            "status": "pending",
        })
    payload = {
        "created_at_utc": datetime.now(UTC).isoformat(),
        "catatan": "Antrian siap untuk webhook integrator auto-post.",
        "posts": posts,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return payload


def send_to_webhook(webhook_url: str, payload: dict) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            return True, f"HTTP {resp.status}"
    except Exception as exc:
        return False, str(exc)


def main() -> None:
    p = argparse.ArgumentParser(description="Full automation affiliate (Bahasa Indonesia)")
    p.add_argument("--product", required=True)
    p.add_argument("--price", required=True, type=float)
    p.add_argument("--problem", default="masalah harian")
    p.add_argument("--hooks", type=int, default=12)
    p.add_argument("--captions", type=int, default=12)
    p.add_argument("--posts", type=int, default=12)
    p.add_argument("--interval", type=int, default=90)
    p.add_argument("--video-duration", type=int, default=12)
    p.add_argument("--audio-dir", default="backsound_indonesia")
    p.add_argument("--output-dir", default="output")
    p.add_argument("--trend-limit", type=int, default=10)
    p.add_argument("--platforms", default="facebook_page,facebook_group,tiktok,instagram")
    p.add_argument("--webhook-url", default="", help="Opsional: kirim payload autopost ke webhook")
    args = p.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    product = Product(args.product, args.price, args.problem)
    trends = get_trending_keywords_id(args.trend_limit)
    backsounds = choose_backsounds(Path(args.audio_dir), max(args.hooks, args.captions, 1), auto_generate=True)
    bs_names = [b.name for b in backsounds]

    hooks, captions = [], []
    for i in range(max(args.hooks, args.captions)):
        t = trends[i % len(trends)]
        b = bs_names[i % len(bs_names)]
        hooks.append(render_list(HOOK_TEMPLATES_ID, 1, product=product.name, price=f"{product.price:.2f}", problem=product.problem, trend=t)[0])
        captions.append(render_list(CAPTION_TEMPLATES_ID, 1, product=product.name, price=f"{product.price:.2f}", problem=product.problem, trend=t, backsound=b)[0])
    hooks, captions = hooks[: args.hooks], captions[: args.captions]

    write_bullets(out / "hooks_id.md", hooks)
    write_bullets(out / "captions_id.md", captions)
    write_bullets(out / "comment_replies_id.md", COMMENT_REPLIES_ID)
    write_bullets(out / "trending_keywords_id.md", trends)
    create_tracker(out / "tracker.csv")
    slots = create_schedule(out / "schedule.csv", datetime.now(UTC), args.posts, args.interval)
    build_content_plan(out / "content_plan.csv", hooks, captions, trends)
    videos = create_videos(out / "videos", hooks, backsounds, args.video_duration)

    platforms = [x.strip() for x in args.platforms.split(",") if x.strip()]
    queue = build_autopost_queue(out / "autopost_queue.json", slots, videos, captions, platforms)

    if args.webhook_url:
        ok, msg = send_to_webhook(args.webhook_url, queue)
        (out / "autopost_delivery.log").write_text(
            f"{datetime.now(UTC).isoformat()} | success={ok} | {msg}\n", encoding="utf-8"
        )

    print(f"Selesai full automation. Output: {out.resolve()}")


if __name__ == "__main__":
    main()
