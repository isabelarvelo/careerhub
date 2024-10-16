# This script assumes that the same row in each csv correspond to the same job. 

import csv
import json
import pymongo
from datetime import datetime
from collections import defaultdict

# Importing Data 
companies_csv = 'mp2-data/companies.csv'
industries_csv = 'mp2-data/industry_info.csv'
jobs_csv = 'mp2-data/jobs.csv'
education_skills_csv = 'mp2-data/education_and_skills.csv'
employment_details_csv = 'mp2-data/employment_details.csv'

# Initialize data structures for new schema
jobs = []
companies = []
industries = []

def get_experience_level(years):
    if years < 2:
        return "Entry Level"
    elif years < 5:
        return "Mid Level"
    else:
        return "Senior Level"

# Helper function to parse list-like strings
def parse_list_string(s):
    return [item.strip() for item in s.strip('"').split(',') if item.strip()]

# Read and process industries data
with open(industries_csv, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    for row in reader:
        industry = {
            "industry_name": row['industry_name'],
            "growth_rate": float(row['growth_rate']),
            "industry_skills": parse_list_string(row['industry_skills']),
            "top_companies": parse_list_string(row['top_companies']),
            "trends": parse_list_string(row['trends'])
        }
        industries.append(industry)



# Reaing in company data 
with open(companies_csv, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    for row in reader:
        company = {
            "company_id": int(row['id']),
            "name": row['name'],
            "size": row['size'],
            "type": row['type'],
            "location": row['location'],
            "website": row['website'],
            "description": row['description'],
            "hr_contact": row['hr_contact'],
            "industry_name": ""  # Will be updated later
        }
        companies.append(company)
    

# Mapping industry id to industry name
industry_id_to_name = {}
with open(industries_csv, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    for row in reader:
        industry_id_to_name[int(row['id'])] = row['industry_name']

# Update company industry_name based on the ID
for company in companies:
    company_id = company['company_id']
    if company_id in industry_id_to_name:
        company['industry_name'] = industry_id_to_name[company_id]
    else:
        company['industry_name'] = "Unknown"

# Read in education and skills 
education_skills = {}
with open(education_skills_csv, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    for row in reader:
        education_skills[int(row['job_id'])] = {
            "required_education": row['required_education'],
            "preferred_skills": parse_list_string(row['preferred_skills'])}


# Read employment details
employment_details = {}
with open(employment_details_csv, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    for row in reader:
        employment_details[int(row['id'])] = {
            "employment_type": row['employment_type'],
            "average_salary": float(row['average_salary']),
            "benefits": parse_list_string(row['benefits']),
            "remote": row['remote'] == 'True',
            "job_posting_url": row['job_posting_url'],
            "posting_date": row['posting_date'],
            "closing_date": row['closing_date']
        }

# Read and process jobs data and populate it with information from other files 
with open(jobs_csv, mode='r', encoding='utf-8-sig') as file:
    reader = csv.DictReader(file)
    for row in reader:
        job_id = int(row['id'])
        years_of_experience = int(row['years_of_experience'])
        company = next((c for c in companies if c['company_id'] == job_id), None)
        emp_details = employment_details.get(job_id, {})
        edu_skills = education_skills.get(job_id, {})

        job = {
            "job_id": job_id,
            "title": row['title'],
            "description": row['description'],
            "detailed_description": row['detailed_description'],
            "responsibilities": parse_list_string(row['responsibilities']),
            "requirements": parse_list_string(row['requirements']),
            "years_of_experience": years_of_experience,
            "experience_level": get_experience_level(years_of_experience),
            "employment_type": emp_details.get('employment_type', ''),
            "average_salary": emp_details.get('average_salary'),
            "benefits": emp_details.get('benefits', []),
            "remote": emp_details.get('remote', False),
            "job_posting_url": emp_details.get('job_posting_url', ''),
            "posting_date": datetime.strptime(emp_details.get('posting_date', ''), '%Y-%m-%d') if emp_details.get('posting_date') else None,
            "closing_date": datetime.strptime(emp_details.get('closing_date', ''), '%Y-%m-%d') if emp_details.get('closing_date') else None,
            "required_education": edu_skills.get('required_education', ''),
            "preferred_skills": edu_skills.get('preferred_skills', []),
        }
        if company:
            job.update({
                "company_id": company['company_id'],
                "company_name": company['name'],
                "company_size": company['size'],
                "company_type": company['type'],
                "company_location": company['location'],
                "company_website": company['website'],
                "company_description": company['description'],
                "company_hr_contact": company['hr_contact'],
                "industry_name": company['industry_name']
            })
        else:
            job.update({
                "company_id": None,
                "company_name": None,
                "company_size": None,
                "company_type": None,
                "company_location": None,
                "company_website": None,
                "company_description": None,
                "company_hr_contact": None,
                "industry_name": None
            })
            
        jobs.append(job)


# Condense industry info to a data structure that contains information about each unique industry 
combined_industry_data = defaultdict(lambda: {
    "growth_rates": [],
    "industry_skills": set(),
    "top_companies": set(),
    "trends": set()
})

for industry in industries:
    name = industry['industry_name']
    combined_industry_data[name]["growth_rates"].append(industry['growth_rate'])
    combined_industry_data [name]["industry_skills"].update(industry['industry_skills'])
    combined_industry_data[name]["top_companies"].update(industry['top_companies'])
    combined_industry_data [name]["trends"].update(industry['trends'])

combined_industry = [
    {
        "industry_name": name,
        "growth_rates": data["growth_rates"],
        "industry_skills": list(data["industry_skills"]),
        "top_companies": list(data["top_companies"]),
        "trends": list(data["trends"])
    }
    for name, data in combined_industry_data.items()
]

# Save dictionarys as json files 

def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

def save_as_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=datetime_serializer)

save_as_json(jobs, 'jobs.json')
save_as_json(combined_industry, 'industries.json')
save_as_json(companies, 'companies.json')

print("All data saved as JSON files.")