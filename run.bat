@echo
chcp 65001
echo 正在启动postgres redis chromadb
docker-compose up -d postgres redis chromadb
pause