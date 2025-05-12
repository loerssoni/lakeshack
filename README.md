## Recruitement task for company x

### Assignment
We have a dataset in an S3 bucket at dwh-fina/billing

The dataset is a collection of CSV files with Hive partitioning. Please create a data pipeline that ingests, preprocesses, aggregates, and outputs this data as insights such as summations, averages, etc on relevant features. You will notice that there are more CSVs added to this dataset dynamically. Your pipeline must take the new files into account and your insights must dynamically update.

### Outputs

The relevant code is pretty included under dags/deploy
* The Airflow DAG used as a base for the orchestration is defined in dags/deploy/dags/dwh_fina.py
* dags/deploy/dags/dwh_fina/extract contains
    * job.yaml - spark job definition
    * schema.json - read in extract to ensure data conforms to predefined schema
    * extract.py
* dags/deploy/dags/dwh_fina/transform contains
    * transform.py which has some boilerplate

### General principle

I want to stick to the spirit of open source and self hosting here. 

Technologies used are open source, and for the most part, the code has been run on my own experimental setup of Airflow + spark on GKE.

We do your basic ELT pattern, striving for a lakehouse architecture, although we do a couple of shortcuts for this implementation.

### Technologies 
We use spark for both extract/load step and the transforms.

##### Airflow
The whole thing is orchestrated as an airflow DAG. This could be any orchestration tool, but you do need one. Iam most familiar with and like Airflow which are the most important factors when on a schedule.

##### Spark
* When going for an open source solution to do data processing at scale, spark provides a lot of versatility and a huge community
    * Versatility and wide support are very important factors when trying to self host os tools
* I have been toying around with running spark + airflow on kuberenetes so I had some infra running for this
    * Partly inspired by the fact that a lot of the pieces are available as managed services the company ^^ 

##### Table format
For table format, we would like to use an open table format (iceberg or delta lake).
These formats enable nice behaviours like
* doing merge instead of overwrite, which is nice for the incremental setup we have here
* time travel if the data evolves, although this data might be somewhat immutable?
* cataloguing and discovery
* possibility to integrate into a downstream bi system

This seemed a bit too much setup for now.

#### Configuration management / deployments
The repo is currently a mess of different stuff around deploying, but one idea would be to have an ansible playbook that:
* copies dag files to a persisted volume (persisted volume is already set up for the cluster)
* ensures that the defined tables are defined in the iceberg catalogue

For build step we should have a separate playbook, so we can use templating and avoid e.g. duplication and make things easy to change and configure
* e.g. job.yaml spark job specs could have a generic template with a couple of things filled from a config
* dag files could include templating as well

### Steps
#### Extract
The extract logic is simple, and in general loading from a cloud storage system has a million available packaged solution. 
Here the idea was to use spark s3a but ran into some issues. 

A couple of bells and whistles are included:
* Incremental load
    * use e.g. boto3 checking file modified timestamps
    * pass some from and to date
        * with airflow, we populate these on regular scheduled run
        * for backfills, we could pass our own date_from and date_to values through dag_run.conf though that is not implemented here
    * ran into some issues with permissions listing the bucket files so this is less than implemented 
* Initial plan was to use the hadoop s3a client for more performant reads, but ran into some permission issues with that one as well.
    * Instead loading with http in to memory, which is not what we would like
        * code comments in extract.py 
* Read to match a predefined schema, we can then do schema evolution as needed
* Since we do a sort of a lakehouse pattern, the "load" is "included" into the extract
    * Here we just (over)write parquet, but we might as well do 

#### Transforms
For transform the idea is to continue to use Spark SQL but this is not fully implemented

Main idea here I think is to take two perspectives an do separate models: The user perspective and the resource perspective.

Some main ideas have been demonstrated  in the notebook under the dwh_fina.

* Prior to transfgormation

A few notes:
* The data here is simple, and we would benefit from having various other sources to complement. 
* We could either do this as a full truncate each time, or as a merge
    * Merge would require an iceberg or deltalake table format and we should pass some info about what files were loaded in this DAG run via XCOM
* Usually I'd like to keep the transform step decoupled from the extract entirely
    * We we usually join data from various sources and usually do various outputs and potentially intermediate steps
    * Here we've orchestrated the transforms into the same DAG since we have a single data source and transforms follows directly
* The demonstration is done via duckdb, which as a side note works very nicely for smaller datasets for interactive analysis (of course, no integration to dashboarding tools, etc.)


#### Extras

* A natural extension here is to use an iceberg table format, mentioned above which provides natural support for both lineage and data catalogues.
* Streaming likely does not make sense for this particular use case, but likely the setup would then be to use spark structured streaming. There should be native support for streaming from an s3 bucket, although  


#### Infra
The infra should be migrated to terraform + ansible or something to that extent. However, some of the infra setup is included in the infra folder for those interested. Mostly spec files applied with kubectl apply are included.
