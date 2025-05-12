FROM spark:3.5.5

USER root

RUN apt-get update && apt-get install -y python3-pip

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

USER spark