.PHONY: all crawl crawl-fresh build build-ana clean

OUT?=out/TEI

all: build

crawl:
	python3 run_pipeline.py --crawl --limit 10

crawl-fresh:
	python3 run_pipeline.py --crawl --limit 10

build:
	python3 run_pipeline.py --out $(OUT)

build-ana:
	python3 run_pipeline.py --out $(OUT) --with_ana

clean:
	rm -rf inbox/cleaned $(OUT)