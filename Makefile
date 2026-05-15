PYTHON ?= python3
SCRIPT := affiliate_automation.py
OUTDIR ?= output_demo
AUDIO_DIR ?= backsound_indonesia_demo

.PHONY: help test run one-output clean

help:
	@echo "Targets:"
	@echo "  make test         - Jalankan unit test"
	@echo "  make run          - Jalankan full automation dengan default demo"
	@echo "  make one-output   - Jalankan dan tampilkan 1 output file (captions_id.md)"
	@echo "  make clean        - Hapus folder output demo"

test:
	$(PYTHON) -m unittest discover -s tests -v

run:
	$(PYTHON) $(SCRIPT) \
		--product "Blender Mini" \
		--price 14.5 \
		--problem "sarapan cepat" \
		--output-dir $(OUTDIR) \
		--audio-dir $(AUDIO_DIR) \
		--hooks 3 \
		--captions 3 \
		--posts 3

one-output: run
	@echo "=== 1 OUTPUT: $(OUTDIR)/captions_id.md ==="
	@sed -n '1,5p' $(OUTDIR)/captions_id.md

clean:
	rm -rf $(OUTDIR) $(AUDIO_DIR)
