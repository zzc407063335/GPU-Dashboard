mkdir logs
mkdir tasks
mkdir data
nosetests --with-coverage --cover-package=DockerApp --cover-html --cover-html-dir=./cover_app test_DockerApp.py -v -s