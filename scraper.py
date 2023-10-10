############################################################
## Functions for scraping and organizing data for website ##
############################################################

import requests
from bs4 import BeautifulSoup
import pandas as pd
from collections import defaultdict
import re
from datetime import datetime, timedelta
import os
import oracledb
from sqlalchemy import create_engine, text
from flask import Flask, render_template
from db import *
import time
import numpy as np


# tracking_all_job_ids = get_all_job_ids_db()


def get_job_results_for_website(title, location, max_years=3, job_count=0):
    ''' This function calls all the other functions to get the job info
        from LinkedIn and the database.'''

    ### FUTURE Mike! Maybe cache ALL the job ids from the database into RAM ###
    global tracking_all_job_ids
    tracking_all_job_ids = get_all_job_ids_db()

    # Scrape ALL pages of LinkedIn for job IDs
    job_ids = get_all_job_ids(title, location)

    # Split job IDs, either they are in the database or need to scrape job details
    job_ids_for_db, job_ids_for_linkedin = split_job_ids(job_ids)
    print(
        f"IDs for db: {len(job_ids_for_db)}   |  IDs for linkedin: {len(job_ids_for_linkedin)}")
    print("Job IDs for the database: ", job_ids_for_db)
    print("Job IDs for LinkedIn scraping: ", job_ids_for_linkedin)

    # Insert job IDs into AWS ETL pipeline: SQS-->Lambda-->DynamoDB
    push_job_ids_to_aws(job_ids_for_linkedin)

    ### REMOVING: NO LONGER QUERYING DB BEFORE SCRAPING. SCRAPING>INSERT INTO DB>QUERY ALL JOB IDS
    # Get job details from the database
    # df_job_details_db = db.get_job_details_db(job_ids_for_db)

    ### REMOVING THIS SECTION BECAUSE THE AWS ETL IS HANDLING THE JOB DETAILS SCRAPING
    # Scrape job details from LinkedIn.
    # Need the title and location to save into the database, maybe need it
    #df_job_details_linkedin = get_job_details_linkedin(title, location, job_ids_for_linkedin)
    # if not df_job_details_db.empty:
    #    print(f"# of details from db: {len(df_job_details_db)}")
    #if not df_job_details_linkedin.empty:
    #    print(f"# of details from linkedin: {len(df_job_details_linkedin)}")

    ### REMOVING: NO LONGER INSERTING INTO ORACLE DATABASE
    # Insert scraped LinkedIn job details into the database
    #insert_job_detail_into_db(df_job_details_linkedin)

    # Add LinkedIn job IDs to the tracking variable
    ### I am NOT caching the job IDs locally, I'm hitting the database on every web request ###
    # tracking_all_job_ids = np.append(job_ids_for_linkedin, tracking_all_job_ids)

    ### REMOVED
    # Converted all the job IDs to a numpy array so I can query it. (Used set() to dedup)
    # job_ids = np.array(list(filter(None, set(job_ids))))
    
    ### NOT SURE IF I NEED TO CONCAT ALL THE JOB IDs, JUST USE the variable:  job_ids
    ### DOES THIS NEED TO BE A NUMPY ARRAY???
    jobs_ids = np.concatenate([job_ids_for_db, job_ids_for_linkedin])

    ### REMOVED: NO LONGER QUERYING ORACLE DATABASE
    # df_all_job_details = pd.concat([df_job_details_db, df_job_details_linkedin])
    # Now I'm pulling all the job details from the database
    #df_all_job_details = query_db_by_id(job_ids, max_years)

    # Query DynamoDB for the job_ids
    l_all_job_details = query_aws_db_by_id(job_ids, max_years)

    ### DEBUGGING
    #print("### HERE IS THE LIST OF DICTIONARIES FROM DYNAMODB ###")
    #for j in l_all_job_details:
    #    print(j)

    # return df_all_job_details.to_dict("records")
    return l_all_job_details

# Sends a request for one page of results to LinkedIn to get a list of job titles
# I do NOT call this function directly, I call get_job_ids, which calls this function


def get_job_results_page(title, location, job_count) -> list:
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    exp_level = "2"  # 2==entry level
    post_date = "r604800"  # r604800==Past week
    # The below url uses exp_level and the job title is enclosed with double quotes
    # url = f'{base_url}?f_E={exp_level}&f_TPR={post_date}&keywords="{title}"&location={location}&start={job_count}'
    # title example: "data" AND "engineer"
    # title = '" AND "'.join(title.split())
    url = f'{base_url}?f_TPR={post_date}&keywords="{title}"&location={location}&start={job_count}'
    print(url)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    all_job_titles = soup.find_all("li")
    return all_job_titles


# Get job ids from one results page
def get_job_ids(title, location, job_count):
    job_ids = []
    all_job_titles = get_job_results_page(title, location, job_count)
    if not all_job_titles:  # if no jobs titles in the list
        print("No job titles found!")
        return None

    # Parses out the job title from one listing
    def parse_job_id(job):
        try:
            job_id = job.find(
                "div", {"class": "base-card"}).get("data-entity-urn").split(":")[3]
            return job_id
        except:
            return ""

    all_job_ids = list(map(parse_job_id, all_job_titles))
    print("Number of jobs on the page: ", len(all_job_ids))
    return all_job_ids

# Get ALL job IDs from ALL result pages


def get_all_job_ids(title, location):
    all_job_ids = []
    job_count = 0
    max_jobs_to_scrape = 100
    # I can't get a job_count for the search query,
    # so going to scrape till it can NOT find any more job ids
    # or I'm going to scrape upto 300 jobs or 12 pages
    while job_count <= max_jobs_to_scrape:
        page_of_ids = get_job_ids(title, location, job_count)
        if page_of_ids:
            all_job_ids.extend(page_of_ids)
        else:
            break
        job_count += 25
        time.sleep(2)

    return all_job_ids

# Split job IDs, if they are in the database or needed to scrape job details


def split_job_ids(job_ids: list) -> tuple:
    # Convert to set to remove duplicates, convert string job ids
    # to ints and convert to numpy array
    job_ids = np.array(list(filter(None, set(job_ids)))).astype('int64')
    # Jobs ids that exist in the database (or being tracked by tracking_all_job_ids)
    job_ids_for_db = job_ids[np.in1d(job_ids, tracking_all_job_ids)]
    # Filter out job ids already in the database
    job_ids_for_linkedin = job_ids[~np.in1d(job_ids, tracking_all_job_ids)]

    return (job_ids_for_db, job_ids_for_linkedin)


# Format strings to be in a consistent format


def string_format(s: str) -> str:
    s = s.replace(" ", "_")
    s = s.replace("'", "")
    s = s.replace('"', "")

    return s


def get_job_details_linkedin(title, location, job_ids: list):
    if isinstance(job_ids, list) and not job_ids:  # No job_ids
        return pd.DataFrame()

    job_url = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}'
    l_all_job_info = []
    sleep_increment = 0

    for id in job_ids:
        d_job_info = {}
        d_job_info["job_id"] = int(id)
        d_job_info["job_search_term"] = title
        d_job_info["location_search_term"] = location
        job_desc_url = job_url.format(id)
        res = requests.get(job_desc_url)
        soup = BeautifulSoup(res.text, "html.parser")

        # If the response code is 429, then we need to slow down scraping
        if res.status_code == 429:
            print("Got blocked by LinkedIn...Slow down!!")
            time.sleep(120)
            continue
        else:
            # Putting in a 2 second delay for scraping
            time.sleep(1+sleep_increment)
            sleep_increment += 0.05

        # Get the company name
        try:
            d_job_info["company"] = soup.find(
                "div", {"class": "top-card-layout__card"}).find("a").find("img").get("alt")
        except:
            d_job_info["company"] = None

        # Get the location
        try:
            d_job_info["location"] = soup.find("div", {"class": "topcard__flavor-row"}).find(
                "span", {"class": "topcard__flavor--bullet"}).text.strip()
        except:
            d_job_info["location"] = ''

        # Get the job title
        try:
            d_job_info["job_title"] = soup.find(
                "h2", {"class": "top-card-layout__title"}).text.strip()
        except:
            d_job_info["job_title"] = ''

        # Get the full job description
        try:
            d_job_info["job_description"] = soup.find(
                "div", {"class": "show-more-less-html__markup"}).get_text(separator=u"\n")
        except:
            d_job_info["job_description"] = ''

        # Get years of experience!!! Keep checking this as it may be buggy
        try:
            d_job_info["experience"] = re.findall(
                # r".*\D\d{1,2}\D.*years?", d_job_info["job_description"])
                r".*\D\d{1,2}\D*(?:years?|yrs)", d_job_info["job_description"])
            d_job_info["experience"] = "\n".join(d_job_info["experience"])
        except:
            d_job_info["experience"] = None

        # Get the max years experience
        if d_job_info["experience"]:
            # print(d_job_info["experience"])
            d_job_info['max_exp'] = max(
                list(map(int, re.findall(r'\d+', d_job_info["experience"]))))

        # Get Seniority level, Employment type, Job function, Industries
        try:
            job_criteria_list = soup.find(
                "ul", {"class": "description__job-criteria-list"}).find_all("li")
            for criteria in job_criteria_list:
                criteria = criteria.text.split("\n")  # convert lines to a list
                # remove lines with only white space
                criteria = [i.strip() for i in criteria if i.strip()]
                criteria[0] = criteria[0].replace(" ", "_").lower()
                d_job_info.update({criteria[0]: criteria[1]})
        except:
            pass

        # Get job posting date
        try:
            posting_date = soup.find(
                "span", {"class": "posted-time-ago__text"}).text.strip()
            posting_num = int(re.match(r'\d{1,2}', posting_date).group())
            if "minute" in posting_date:
                d_job_info["posting_date"] = datetime.today() - \
                    timedelta(minutes=posting_num)
            elif "hour" in posting_date:
                d_job_info["posting_date"] = datetime.today() - \
                    timedelta(hours=posting_num)
            elif "day" in posting_date:
                d_job_info["posting_date"] = datetime.today() - \
                    timedelta(days=posting_num)
            elif "week" in posting_date:
                d_job_info["posting_date"] = datetime.today() - \
                    timedelta(days=posting_num*7)
            else:
                d_job_info["posting_date"] = ""

        except:
            d_job_info["posting_date"] = ''

        # !!! Get Other useful info with AI !!!

        # Get URL
        try:
            d_job_info["url"] = soup.find(
                "a", {"class": "topcard__link"}).get("href")
        except:
            d_job_info["url"] = None

        # Append the job info (dict) to the list of job info
        l_all_job_info.append(d_job_info)

    # Convert list of all job info dicts to a dataframe
    df_all_job_info = pd.DataFrame(l_all_job_info)
    return df_all_job_info
