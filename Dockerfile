FROM python:3.9-alpine as python

RUN mkdir /root/DTS-aggregator
WORKDIR /root/DTS-aggregator

COPY ["./", "./"]

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["flask", "run", "--host=0.0.0.0"]