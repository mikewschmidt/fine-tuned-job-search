########################################################
## Functions for connecting and querying the database ##
########################################################


import pandas as pd
import numpy as np
import re
import os
import oracledb
from sqlalchemy import create_engine

# Setting variables and creating the connection engine
cs = '''(description= (retry_count=20)(retry_delay=3)(address=(protocol=tcps)(port=1521)(host=adb.us-sanjose-1.oraclecloud.com))(connect_data=(service_name=ga3e236c6957ba6_oltpdb_high.adb.oraclecloud.com))(security=(ssl_server_dn_match=yes)))'''
user = "appuser"
password = os.environ['ORACLE_PASSWORD_APPUSER']
engine = create_engine(
    f'oracle+oracledb://{user}:{password}@{cs}'
)

# Query database with title and location


def query_db(title, location):
    with engine.connect() as conn:
        df_results = pd.read_sql_query(
            f"SELECT * FROM tbl_jobs WHERE job_title like '%{title}%' AND location like '%{location}%'", conn)
        # results = conn.execute(text(f"SELECT * FROM tbl_jobs WHERE job_title like '%{title}%' AND location like '%{location}%'"))
        results = df_results.to_dict("records")
    return results

# Get all the jobs in the database


def get_all_job_ids():
    with engine.connect() as conn:
        tracking_all_job_ids = pd.read_sql_query(
            f'SELECT job_id FROM tbl_jobs', conn)
    return tracking_all_job_ids.to_numpy()

# Get job details in the database by job IDs


def get_job_details_db(job_ids: np.ndarray) -> pd.DataFrame:
    if len(job_ids) == 1:
        job_ids = f"({job_ids[0]})"
    else:
        job_ids = tuple(job_ids)

    with engine.connect() as conn:
        df_results = pd.read_sql_query(
            f"SELECT * FROM tbl_jobs WHERE job_id in {job_ids}", conn)
    return df_results