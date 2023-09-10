import requests
from bs4 import BeautifulSoup
import math

title = "'data engineer'"
location = "St. Louis, MO"
job_count = 0

url = f"https://www.linkedin.com/jobs/api/seeMoreJobPostings/search?keywords={title}&location={location}&start={job_count}"

print(url)
