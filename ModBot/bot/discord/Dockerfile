FROM python:3.12-slim

WORKDIR /app

COPY discord/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code is mounted via docker-compose volumes
CMD ["python", "-m", "discord_bot.main"]
