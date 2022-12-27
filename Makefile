init:
	poetry install

test: clean init
	poetry install --with test
	python3 -m pylint gocker/ test/

test-e2e: clean init
	gocker --shortcut-list

clean:
	find . -name "__pycache__" | xargs rm -r

dev-up:
	docker-compose  -f $$PWD/test/docker-compose.yml up -d --build
	docker-compose  -f $$PWD/test/docker-compose.yml ps

dev-down:
	docker-compose  -f $$PWD/test/docker-compose.yml down
	docker-compose  -f $$PWD/test/docker-compose.yml ps
