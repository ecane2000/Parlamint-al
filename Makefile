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
