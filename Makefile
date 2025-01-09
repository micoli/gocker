init:
	poetry install

test: clean init
	poetry install --with test
	python3 -m pylint gocker/ test/

test-e2e: clean init
	gocker --action shortcut-list

test-installation:
	docker run -it -v $$PWD/test:/app python:3.10 bash -c /app/installation.sh

clean:
	find . -name "__pycache__" | xargs rm -r

dev-up:
	docker-compose  -f $$PWD/test/docker-compose.yml up -d --build
	docker-compose  -f $$PWD/test/docker-compose.yml ps

dev-down:
	docker-compose  -f $$PWD/test/docker-compose.yml down
	docker-compose  -f $$PWD/test/docker-compose.yml ps
