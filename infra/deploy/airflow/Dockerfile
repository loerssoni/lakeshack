FROM apache/airflow:2.9.1-python3.11

USER root

COPY requirements.txt /var/airflow/requirements.txt

WORKDIR /var/airflow

RUN mkdir -p /var/airflow/plugins
RUN chmod -R 777 /var/airflow/plugins
COPY plugins/. /var/airflow/plugins/

USER airflow

RUN pip install \
    --no-cache-dir \
    -r /var/airflow/requirements.txt