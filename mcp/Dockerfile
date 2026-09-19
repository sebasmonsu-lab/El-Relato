FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir "mcp>=2,<3"
EXPOSE 8000
CMD ["python", "mcp/server.py"]
