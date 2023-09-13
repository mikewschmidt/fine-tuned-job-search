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
import db
import time
import numpy as np


# Sends a request for one page of results to LinkedIn to get a list of job titles
def get_job_results_page(title, location, job_count) -> list:
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    exp_level = "2"  # 2==entry level
    post_date = "r604800"  # r604800==Past week
    url = f'{base_url}?f_E={exp_level}&f_TPR={post_date}&keywords="{title}"&location={location}&start={job_count}'
    print("job page URL: ", url)
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    all_job_titles = soup.find_all("li")
    return all_job_titles

# Parses out the job title from one listing


def parse_job_id(job):
    return job.find("div", {"class": "base-card"}).get("data-entity-urn").split(":")[3]

# Get all job ids from one results page


def get_job_ids(title, location, job_count):
    job_ids = []
    all_job_titles = get_job_results_page(title, location, job_count)
    if not all_job_titles:  # if no jobs titles in the list
        print("No job titles found!")
        return None

    all_job_ids = list(map(parse_job_id, all_job_titles))
    print("all job ids: ", all_job_ids)
    return all_job_ids

# Format strings to be in a consistent format


def string_format(s: str) -> str:
    s = s.replace(" ", "_")
    s = s.replace("'", "")
    s = s.replace('"', "")

    return s


def get_job_details_linkedin(job_ids):
    job_url = 'https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}'
    l_all_job_info = []

    for id in job_ids:
        d_job_info = {}
        d_job_info["job_id"] = int(id)
        d_job_info["job_search_term"] = title
        d_job_info["location_search_term"] = location
        job_desc_url = job_url.format(id)
        print(job_desc_url)
        res = requests.get(job_desc_url)
        soup = BeautifulSoup(res.text, "html.parser")

        # If the response code is 429, then we need to slow down scraping
        if res.status_code == 429:
            print("Got blocked LinkedIn...Slow down!!")
            time.sleep(120)
        else:
            # Putting in a 2 second delay for scraping
            time.sleep(2)

        # Get the company name
        d_job_info["company"] = soup.find(
            "div", {"class": "top-card-layout__card"}).find("a").find("img").get("alt")

        # Get the location
        d_job_info["location"] = soup.find("div", {"class": "topcard__flavor-row"}).find(
            "span", {"class": "topcard__flavor--bullet"}).text.strip()

        # Get the job title
        d_job_info["job_title"] = soup.find(
            "h2", {"class": "top-card-layout__title"}).text.strip()

        # Get the full job description
        d_job_info["job_description"] = soup.find(
            "div", {"class": "show-more-less-html__markup"}).get_text(separator=u"\n")

        # Get years of experience!!! Keep checking this as it may be buggy
        d_job_info["experience"] = re.findall(
            r".*\D\d{1,2}\D.*years?", d_job_info["job_description"])
        d_job_info["experience"] = "\n".join(d_job_info["experience"])

        # Get the max years experience
        if d_job_info["experience"]:
            d_job_info['max_exp'] = max(re.findall(
                r'\d{1,2}', d_job_info["experience"]))

        # Get Seniority level, Employment type, Job function, Industries
        job_criteria_list = soup.find(
            "ul", {"class": "description__job-criteria-list"}).find_all("li")
        for criteria in job_criteria_list:
            criteria = criteria.text.split("\n")  # convert lines to a list
            # remove lines with only white space
            criteria = [i.strip() for i in criteria if i.strip()]
            criteria[0] = criteria[0].replace(" ", "_").lower()
            d_job_info.update({criteria[0]: criteria[1]})

        # Get job posting date
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
        else:
            d_job_info["posting_date"] = ""

        # !!! Get Other useful info with AI !!!

        # Get URL
        d_job_info["url"] = soup.find(
            "a", {"class": "topcard__link"}).get("href")
        print(d_job_info["url"])

        # Append the job info (dict) to the list of job info
        l_all_job_info.append(d_job_info)

    # Convert list of all job info dicts to a dataframe
    df_all_job_info = pd.DataFrame(l_all_job_info)
    df_all_job_info
