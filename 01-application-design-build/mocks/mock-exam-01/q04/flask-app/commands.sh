docker build -t flask-app:1.0 .

docker images flask-app

docker run -d -p 5000:5000 --name flask-container flask-app:1.0

docker ps -a | grep flask-container

docker logs flask-container

docker exec -it flask-container bash

sleep 5 curl http://localhost:5000/api/v1/resource
exit

docker stop flask-container

docker rm -f flask-container

