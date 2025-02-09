
FROM python:3.9-slim

WORKDIR /app

RUN apt update && apt install -y iproute2 & rm -rf /var/lib/apt/lists/*

COPY ip_tool.py /app/ip_tool.py

RUN chmod +x /app/ip_tool.py

CMD ["python3", "/app/ip_tool.py"]
