########################################################
## Functions for connecting and querying the database ##
########################################################


import pandas as pd
import numpy as np
import re
import os
import oracledb
from sqlalchemy import create_engine
import boto3


# Setting variables and creating the connection engine
### NOT USING ORACLE RIGHT NOW
#conn_str = '''(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.us-sanjose-1.oraclecloud.com))(connect_data=(service_name=ga3e236c6957ba6_oltpdb_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'''
#user = "appuser"
#password = os.environ['ORACLE_PASSWORD_APPUSER']
#engine = create_engine(
#    f'oracle+oracledb://{user}:{password}@{conn_str}'
#)


# Query database with title and location

### NOT USING ORACLE RIGHT NOW
'''
def query_db(title, location) -> list:
    title = title.replace(" ", "%")
    with engine.connect() as conn:
        df_results = pd.read_sql_query(
            f"""SELECT * 
            FROM tbl_jobs 
            WHERE lower(job_title) like '%{title.lower()}%' 
            AND lower(location) like '%{location.lower()}%'
            ORDER BY posting_date DESC""", conn)
        # results = conn.execute(text(f"SELECT * FROM tbl_jobs WHERE job_title like '%{title}%' AND location like '%{location}%'"))
        results = df_results.to_dict("records")
    return results
'''

# Query database by id
### NOT USING ORACLE RIGHT NOW
'''
def query_db_by_id(job_ids: np.ndarray, max_years: int) -> pd.DataFrame:
    # Convert it into a tuple or if there is 1 job ID, then just get that
    if len(job_ids) == 1:
        job_ids = f"({job_ids[0]})"
    else:
        job_ids = tuple(job_ids)

    print("MAX YEARS: ", max_years)

    with engine.connect() as conn:
        df_results = pd.read_sql_query(
            f"""SELECT * 
            FROM tbl_jobs 
            WHERE job_id in {job_ids} 
            AND max_exp <= {max_years} 
            ORDER BY posting_date DESC""", conn)
    return df_results
'''

# Get all the job IDs in the database, to keep it in RAM


def get_all_job_ids_db():
    
    dynamodb = boto3.resource('dynamodb', region_name="us-east-2",
                                aws_access_key_id=os.environ['WEBAPP_AWS_ACCESS_KEY_ID'],
                                aws_secret_access_key=os.environ['WEBAPP_AWS_SECRET_ACCESS_KEY'])
    table = dynamodb.Table("linkedin_jobs")

    response = table.scan(AttributesToGet=['job_id'])
    tracking_all_job_ids = [int(id['job_id']) for id in response['Items']]
    tracking_all_job_ids = np.array(tracking_all_job_ids)
    
    #with engine.connect() as conn:
    #    tracking_all_job_ids = pd.read_sql_query(
    #        f'SELECT job_id FROM tbl_jobs', conn)
    return tracking_all_job_ids


# Get job details in the database by job IDs

### NOT USING ORACLE RIGHT NOW
'''
def get_job_details_db(job_ids: np.ndarray) -> pd.DataFrame:
    if not np.any(job_ids):  # No job_ids
        return pd.DataFrame()

    if len(job_ids) == 1:
        job_ids = f"({job_ids[0]})"
    else:
        job_ids = tuple(job_ids)

    with engine.connect() as conn:
        df_results = pd.read_sql_query(
            f"SELECT * FROM tbl_jobs WHERE job_id in {job_ids}", conn)
    return df_results
'''

# Insert scraped Linkedin into the database
### NOT USING ORACLE RIGHT NOW
'''
def insert_job_detail_into_db(df_job_info: pd.DataFrame):
    if isinstance(df_job_info, pd.DataFrame) and not df_job_info.empty:
        df_job_info.to_sql('tbl_jobs', engine, 'appuser',
                           if_exists='append', index=False, method=None)
'''

# Scrape and Insert job details into AWS ETL:  SQS --> Lambda --> DynamoDB
def push_job_ids_to_aws(job_ids: list):
    client = boto3.resource('sqs',
                            endpoint_url='https://sqs.us-east-2.amazonaws.com/762907089775/job_ids',
                            region_name='us-east-2',
                            aws_access_key_id=os.environ['WEBAPP_AWS_ACCESS_KEY_ID'],
                            aws_secret_access_key=os.environ['WEBAPP_AWS_SECRET_ACCESS_KEY'])

    queue = client.get_queue_by_name(QueueName='job_ids')
    for id in job_ids:
        response = queue.send_message(MessageBody=f'{id}')


# Query DynamoDB by id


def query_aws_db_by_id(job_ids: np.ndarray, max_years: int) -> list:
    # Create the DynamoDB table object
    l_all_job_details = []
    dynamodb = boto3.resource('dynamodb', region_name="us-east-2",
                              aws_access_key_id=os.environ['WEBAPP_AWS_ACCESS_KEY_ID'],
                              aws_secret_access_key=os.environ['WEBAPP_AWS_SECRET_ACCESS_KEY'])
    table = dynamodb.Table("linkedin_jobs")
    for id in job_ids:
        response = table.get_item(Key={"job_id": int(id)})
        # Future Mike, maybe you should filter this out at the db layer
        if response and response.get("Item", None):
            max_exp = response["Item"].get("max_exp", 0)
            if max_exp and max_exp <= max_years:
                l_all_job_details.append(response["Item"])
        else:
            print("No db Response!! for job_id: ", id)

    return l_all_job_details
