# Fine-Tuned Job Search
#### The jobs you're looking for... Nothing More!
http://jobsfor.us.to  


## ** [[ **This is a work in progress** ]] **

## Marketing Pitch
Tired of wasting time sifting through endless job postings with TOO MANY results that don't match your expertise?
Look no further! Our simple website takes the hassle out of job hunting by filtering out irrelevant listings, leaving you with only the opportunities that perfectly fit your preferences and experience. 
With a click of a button, you can uncover your dream job and start making strides toward the career you've always wanted. Why settle for **__MORE__** when you can get **__LESS__** to seamlessly find what you're truly looking for? Visit our site **NOW!** and revolutionize your job search experience.

## Architecture
![Fine-Tuned Job Search diagram](https://github.com/mikewschmidt/fine-tuned-job-search/blob/master/templates/fine-tuned-job-search.drawio.png "Fine-Tuned Job Search diagram")

When submitting a job search, the app submits a more targeted search on the large job search website. Scrapes the job IDs from the resultset and pushes them to the SQS queue. Then a Lambda trigger executes the code to scrape the job details and writes it to the DynamoDB database.

As mentioned, this is a work in progress; the next steps will be a user login and job tracking.


## Technologies
The technologies used in this project:
- AWS SQS (Simple Queue Service)
- AWS Lambda
- AWS DynamoDB (NoSQL database)
- Oracle Cloud Compute
  - Flask framework (front-end)
- Python ETL
  - Beautiful Soup (Web Scraping)
  - Pandas
  - urllib
  - Boto3
