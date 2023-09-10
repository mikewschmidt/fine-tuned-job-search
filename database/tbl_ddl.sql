-- Run as Admin
alter user appuser quota unlimited on data;


CREATE TABLE APPUSER.tbl_jobs 
    ( 
     job_id          NUMBER PRIMARY KEY, 
     company         VARCHAR2 (50)  NOT NULL, 
     location        VARCHAR2 (100) NOT NULL, 
     job_title       VARCHAR2 (200) NOT NULL, 
     job_description VARCHAR (4000) NOT NULL, 
     experience      VARCHAR2 (500) , 
     Seniority_level VARCHAR2 (20) , 
     Employment_type VARCHAR2 (20) , 
     Job_function    VARCHAR2 (50) , 
     Industries      VARCHAR2 (100) , 
     posting_date    TIMESTAMP NOT NULL, 
     url             VARCHAR2 (100) NOT NULL
    ) 
;


INSERT INTO appuser.tbl_jobs VALUES (
    9999,
    'test company',
    'pleasentville',
    'job_title',
    'job description',
    'experience',
    'entry-level',
    'full time',
    'job function junction',
    'pimpin',
    TRUNC(CURRENT_DATE),
    'www.pimpinainteasy.com'
)
;