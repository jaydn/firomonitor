FROM python:latest

WORKDIR /scraper

COPY firomon-scraper/Requirements.txt ./
RUN pip install --no-cache-dir -r Requirements.txt

COPY firomon-scraper/ /scraper
COPY shared/ /shared

CMD [ "python", "main.py" ]
