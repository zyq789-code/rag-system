chcp 65001
echo 正在激活虚拟环境...
call venv\Scripts\activate.bat

rem HuggingFace 模型已手动缓存，本机镜像对 python 客户端拦截，强制离线加载
set HF_HUB_OFFLINE=1
set TRANSFORMERS_OFFLINE=1

echo 正在启动 Uvicorn 服务器...
uvicorn main:app --reload --port 8080

pause