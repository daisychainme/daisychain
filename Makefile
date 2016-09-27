PYTHON = ../virtualenv/bin/python
COVERAGE = ../virtualenv/bin/coverage
BASE = ./daisychain
SETTINGS = config.settings_local

run:
	cd $(BASE) && $(PYTHON) ./manage.py runserver --settings=$(SETTINGS)

startapp:
	cd $(BASE) && $(PYTHON) ./manage.py startapp $(APPNAME) --settings=$(SETTINGS)

makemigrations:
	cd $(BASE) && $(PYTHON) ./manage.py makemigrations --settings=$(SETTINGS)

migrate:
	cd $(BASE) && $(PYTHON) ./manage.py migrate --settings=$(SETTINGS)

loaddata:
	cd $(BASE) && $(PYTHON) ./manage.py loaddata initial_data.json --settings=$(SETTINGS)

test:
	cd $(BASE) && $(PYTHON) ./manage.py test $(APPNAME) --settings=$(SETTINGS)

coverage:
	cd $(BASE) && $(COVERAGE) run ./manage.py test $(APPNAME) --settings=$(SETTINGS)

report:
		cd $(BASE) && $(COVERAGE) report

html:
	cd $(BASE) && $(COVERAGE) html

shell:
	cd $(BASE) && $(PYTHON) ./manage.py shell --settings=$(SETTINGS)

initial_data:
	cd $(BASE) && $(PYTHON) ./manage.py loaddata initial_data.json --settings=$(SETTINGS)
