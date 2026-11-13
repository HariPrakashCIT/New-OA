FROM python:3.12-slim
WORKDIR /app
COPY model-hosting/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY model-hosting/server.py ./server.py
RUN mkdir /cache && chown -R 10001:10001 /cache /app
ENV HF_HOME=/cache
USER 10001
EXPOSE 8000
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8000"]
