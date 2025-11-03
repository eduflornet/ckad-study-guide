docker build -t secure-app .

docker run -d -p 5003:5000 --name secure-app-test secure-app

sleep 3 && curl -s http://localhost:5003

curl -s http://localhost:5003/whoami

docker images secure-app

$HOME/.local/bin/trivy image secure-app --severity HIGH,CRITICAL --quiet

docker stop secure-app-test && docker rm secure-app-test
