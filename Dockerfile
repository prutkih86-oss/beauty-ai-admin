FROM python:3.13-slim
WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt

RUN useradd -u10111 -m adminpanel

COPY  . .

RUN chown -R adminpanel:adminpanel /app

USER adminpanel

EXPOSE 8080

CMD ["python", "main.py"]