venv:
	@echo "creating Virtualenv..."
	virtualenv -p python3 venv
	. venv/bin/activate; \
	pip install --upgrade pip setuptools; \
	pip install -r requirements.txt;

build: venv
	@echo "creating Application..."
	. venv/bin/activate; \
	pip install -U pyinstaller; \
	pyinstaller --console --windowed --onefile --name=pionUploader pionUploader.py --icon=/images/pion.ico;

clean: 
	@echo "cleaning..."
	@rm -f *.spec
	@rm -rf __pycache__
	@rm -rf build
	@rm -rf dist


run: venv
	. venv/bin/activate; \
	python3 pionUploader.py;

bdist:
	@echo "building bdist_wheel..."
	python3 setup.py sdist bdist_wheel;

test_publish: clean bdist
	@echo "uploading to test pypi..."
	python3 -m twine upload --repository testpypi dist/*;

publish: clean bdist
	@echo "uploading to pypi..."
	python3 -m twine upload dist/*;


