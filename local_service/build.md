## build command
docker build -t gpudashboard:v0.1.0 --build-arg UID=`id -u` --build-arg GID=`id -g` .