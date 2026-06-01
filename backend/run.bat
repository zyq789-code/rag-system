chcp 65001
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

echo 正在启动 Uvicorn 服务器...
uvicorn main:app --reload --port 8080

pause