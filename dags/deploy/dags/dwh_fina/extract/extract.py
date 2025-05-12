




from pyspark.sql import SparkSession, types
from pyspark import SparkFiles


import json
from datetime import datetime
import pytz

def dt_from_str(date):
    dt = datetime.strptime(date, "%Y-%m-%d")
    return dt.replace(tzinfo=pytz.UTC)

def load_schema_from_json(json_path: str) -> types.StructType:
    with open(json_path, "r") as file:
        schema_def = json.loads(file.read())

    field_type_map = {
        "string": types.StringType(),
        "integer": types.IntegerType(),
        "double": types.DoubleType(),
        "boolean": types.BooleanType(),
        "timestamp": types.TimestampType(),
    }

    fields = [
        types.StructField(
            field["name"],
            field_type_map[field["type"].lower()],
            field.get("nullable", True)
        )
        for field in schema_def["fields"]
    ]

    return types.StructType(fields)

def get_s3_files_between_dates(date_from, date_to, bucket, endpoint_url):

    import pandas as pd
    daterange  = pd.date_range(date_from, date_to,  freq='d').to_pydatetime()
    return [
        # f"s3a://dwh-fina/billing/year={dt.year}/month={str(dt.month).zfill(2)}/day={str(dt.day).zfill(2)}/billing.csv" for dt in daterange
        # s3a seems to not be supported either so let's just go ahead and load through http...
        
        f"https://{endpoint_url}/{bucket}/billing/year={dt.year}/month={str(dt.month).zfill(2)}/day={str(dt.day).zfill(2)}/billing.csv" for dt in daterange
    ]

    ### Something like below should work if we are allowed to list objects but here we run into Access denied
    ## So to get going let's instead return just the hive partition files matching the particular dates for now:

    import boto3
    from botocore import UNSIGNED
    from botocore.config import Config

    
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED), endpoint_url=endpoint_url)
    included_files = []
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket):
        for obj in page.get('Contents', []):
            last_modified = obj['LastModified']
            if dt_from <= last_modified <= dt_to:
                included_files.append({"name":obj["Key"], "lastModified": last_modified})
    return included_files

def main():
    # pass these
    bucket = "dwh-fina"
    endpoint_url = "f7r4a.upcloudobjects.com"
    date_from = "2025-05-10"
    date_to = "2025-05-11"

    spark = SparkSession.builder \
        .appName("fina-gcs-write") \
        .getOrCreate()

    # this path we should generate dynamically
    schema = load_schema_from_json("/var/airflow/dags/dwh_fina/extract/schema.json")

    # get files to fetch
    files = get_s3_files_between_dates(date_from, date_to, bucket, endpoint_url)
    print(f"Retrieving csvs: {files}")
    # df = (
    #     spark.read
    #     .schema(schema)
    #     .option("recursiveFileLookup", True)
    #     .option("header", True)
    #     .csv(files)
    # )

    # Since we lake the s3a functionality, let's do a quick solve:
    df = spark.createDataFrame([], schema)
    import pandas as pd
    for f in files:
        print("reading file", f)
        pdf = pd.read_csv(f)
        pyspark_df = spark.createDataFrame(pdf)
        df = df.union(pyspark_df)    

    # If we really would be going for a more http based solution hen we would likely want to
    # do some request handling and retries here and do files in parallel etc. and probably
    # just use python.
    
    # However the "native" s3 read would be ideal here of course.

    

    # Write to parquet
    # Here, for added functionality, we should use an open table format like
    # iceberg (or delta lake), but that looks to be too much set up for this exercise
    df.write \
    .mode("overwrite") \
    .partitionBy(["year", "month", "day"]) \
    .option("path", "gs://lakeshack-dev-airflow/dwh/fina") \
    .save()

    spark.stop()

if __name__ == "__main__":
    main()