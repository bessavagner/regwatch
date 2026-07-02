.PHONY: test

test:
	DJANGO_DEBUG=1 uv run pytest $(ARGS)
