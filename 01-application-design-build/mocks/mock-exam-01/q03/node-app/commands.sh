
docker build -t node-app:1.0 .

docker build -t node-app:latest .

docker build -t node-app:production .

docker images node-app

docker save -o node-app.tar node-app:latest    