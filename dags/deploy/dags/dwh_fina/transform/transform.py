




from pyspark.sql import SparkSession

def main():
    # pass these
    bucket = "dwh-fina"
    endpoint_url = "f7r4a.upcloudobjects.com"
    date_from = "2025-05-10"
    date_to = "2025-05-11"

    spark = SparkSession.builder \
        .appName("fina-transform") \
        .getOrCreate()

    # Would be nicer to have a separate sql
    spark.sql("""
              
              
    """)

    spark.stop()

if __name__ == "__main__":
    main()