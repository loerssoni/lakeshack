from datetime import timedelta, datetime


from airflow import DAG

from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.utils.dates import days_ago


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': days_ago(1),
    'email': ['airflow@example.com'],
    'email_on_failure': False,
    'email_on_retry': False,
    'max_active_runs': 1,
    'retries': 0,
}

with DAG(
    dag_id='spark_test_dag',
    start_date=days_ago(1),
    default_args=default_args,
    schedule=None,
    tags=['example']
) as dag:
    extract = SparkKubernetesOperator(
        task_id='spark_example',
        namespace='airflow',
        application_file='{{ "/var/airflow/dags/dwh_fina/extract/job.yaml" }}',
        kubernetes_conn_id='kubernetes_default',
        do_xcom_push=True,
    )
    transform = SparkKubernetesOperator(
        task_id='spark_example',
        namespace='airflow',
        application_file='{{ "/var/airflow/dags/dwh_fina/transform/job.yaml" }}',
        kubernetes_conn_id='kubernetes_default',
        do_xcom_push=True,
    )
    extract >> transform
