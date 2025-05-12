# deployment util to quickly copy over dag files to cluster for testings
POD=$(kubectl get pods -n airflow -l app=airflow -o custom-columns=":metadata.name" | grep 'deploy-airflow-scheduler')
kubectl cp ./dags/. airflow/$POD:/var/airflow/dags/