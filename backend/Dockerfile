FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
# 大陆部署走阿里云 pip 源加速；海外可构建时传 --build-arg PIP_INDEX_URL=https://pypi.org/simple
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/
RUN pip install --no-cache-dir -r requirements.txt --index-url ${PIP_INDEX_URL}
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
