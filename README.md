# Full Automation Affiliate (Bahasa Indonesia)

Tools ini dibuat untuk workflow **full automation**:

1. Automated trending keyword search (Indonesia)
2. Generate konten (hook, caption, script balasan)
3. Auto generate backsound (jika folder audio kosong)
4. Generate video konten
5. Siapkan queue automatic post ke:
   - Facebook Page
   - Facebook Group
   - TikTok
   - Instagram
6. (Opsional) kirim queue ke webhook integrator (Make/Zapier/n8n/custom API)

## Jalankan

```bash
python3 affiliate_automation.py \
  --product "Blender Mini" \
  --price 14.5 \
  --problem "sarapan cepat" \
  --output-dir output \
  --audio-dir backsound_indonesia
```

Dengan webhook:

```bash
python3 affiliate_automation.py \
  --product "Blender Mini" \
  --price 14.5 \
  --problem "sarapan cepat" \
  --webhook-url "https://example.com/autopost"
```

## Output

- `trending_keywords_id.md`
- `hooks_id.md`
- `captions_id.md` (caption include backsound)
- `comment_replies_id.md`
- `content_plan.csv`
- `tracker.csv`
- `schedule.csv`
- `videos/short_*` (`.mp4` jika ffmpeg ada, `.txt` jika tidak)
- `autopost_queue.json`
- `autopost_delivery.log` (jika pakai webhook)

## Catatan Auto Post

Posting langsung ke Facebook/TikTok/Instagram butuh API resmi + token akun bisnis.
Script ini menyiapkan payload otomatis dan bisa langsung dihubungkan ke automation pipeline Anda.
