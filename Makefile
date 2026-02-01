.PHONY: all crawl build build-ana clean

OUT?=out

all: build

crawl:
	python -m src.crawl --out inbox

build:
	python -m src.pipeline --out $(OUT)

build-ana:
	python -m src.pipeline --out $(OUT) --with-ana

clean:
	rm -rf inbox $(OUT)

# Process existing files
python3 run_pipeline.py
# Crawl fresh PDFs + process
python3 run_pipeline.py --crawl --limit 10