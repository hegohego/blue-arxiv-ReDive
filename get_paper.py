#https://pypi.org/project/arxiv/

import arxiv
import yaml
import os
import csv
import psycopg2

def au_search(author):
  search = arxiv.Search(query ='au:"'+author+'"',max_results = 1,sort_by = arxiv.SortCriterion.SubmittedDate)
  return search

def read_config(file_dir):
    
    config_path = f'{file_dir}/config/authors_config.yaml' # file dir
    with open(config_path, 'r') as yml:
        authors = yaml.safe_load(yml)
        
    return authors["authors"]

def get_connection():
    dsn = os.environ.get('DATABASE_URL')
    return psycopg2.connect(dsn)

def read_db():
    with get_connection() as conn:
        with conn.cursor() as cur:

            post_short_ids = []
            cur.execute('SELECT * FROM papers')
            for row in cur:
                post_short_ids.append(row[0])
    return post_short_ids

def check_db(file_dir,s_id):
    post_ids = read_db()
    
    if s_id in post_ids:
        return False
    else:
        return True
    
def write_db(new_ids):
    with get_connection() as conn:
        with conn.cursor() as cur:
            for new_id in new_ids:
                cur.execute('INSERT INTO papers (short_id) VALUES (%s)', (new_id,))
                
import time
import datetime
from dateutil import tz
timefilter_threshold = 1

def time_filter(published):# not use 
    JST = tz.gettz('Asia/Tokyo')
    UTC = tz.gettz("UTC")

    now = datetime.datetime.now(JST)
    now_utc = now.astimezone(UTC)

    time_diff = now_utc - published
    
    if datetime.timedelta(days=timefilter_threshold) >= time_diff:
        return True
    else:
        return False    

def get_paper():
    
    file_abs_path = os.path.abspath(__file__)
    file_dir = os.path.dirname(file_abs_path)
    
    authors = read_config(file_dir)
    
    papers = []
    new_ids = []
    
    for author in authors:
      search = au_search(author)
      for result in search.results():
          
        s_id = result.get_short_id()
        
        paper = {"author" : author,\
                 "title" : result.title,\
                 "published" : result.published,\
                 "url" : result.pdf_url }
            
        if check_db(file_dir, s_id):
            papers.append(paper)
            new_ids.append(s_id)
            
    if len(new_ids) != 0:
        write_db(new_ids)
        
    return papers

if __name__ == "__main__":
    papers = get_paper()
    
    print(len(papers))
    
    for paper in papers:
        print(paper)

