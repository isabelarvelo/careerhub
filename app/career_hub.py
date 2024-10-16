'''Module for serving API requests'''

# Import libraries 
from app import app 
from bson.json_util import dumps, loads
from bson import ObjectId
from flask import request, jsonify
import json
import ast 
from importlib.machinery import SourceFileLoader
from pymongo import MongoClient
from bson.objectid import ObjectId
from bson.errors import InvalidId
from datetime import datetime



# 1. Connect to the client 
client = MongoClient("mongodb://mongodb:27017/") 

# Import the utils module
utils = SourceFileLoader('*', './app/utils.py').load_module() # load in functions in utils.py

# 2. Select the database
db = client.careerhub 

from app import utils 


@app.route("/")
def get_initial_response():
    """
    Initial entry point for the API, providing a friendly welcome message and basic API information.

    Endpoint: http://localhost:5001/

    Returns:
        JSON: A welcome message containing the API version, status, and greeting.
    """

    welcome_message = {
        'apiVersion': 'v1.0',
        'status': '200',
        'message': 'Welcome to the Career Hub API!',
        'endpoints': [
            {
                'path': '/create/jobPost',
                'method': 'POST',
                'description': 'Create a new job posting'
            },
            {
                'path': 'search_by_job_id /<job_id>',
                'method': 'GET',
                'description': 'View Job Details'
            }, 
            {
                'path': '/update_by_job_title',
                'method': 'POST',
                'description': 'Update job details'
            }, 
            {
            'path': '/delete_by_job_title',
            'method': 'POST',
            'description': 'Remove job listing'
            },
            {
            'path': '/jobs_by_salary',
            'method': 'GET',
            'description': 'Get jobs within a specified salary range'

            },
            {
            'path': '/jobs_by_experience',
            'method': 'GET',
            'description': 'Get jobs by experience level'
            },
            {
                'path': '/top_companies_by_industry',
                'method': 'GET',
                'description': 'Fetch top companies in a given industry'
            }
        ],
        'note': 'All POST endpoints provide detailed instructions when accessed with a GET request'

    }
    return jsonify(welcome_message), 200




@app.route("/create/jobPost", methods=['POST', 'GET'])
def create_job_post():
    """
    User can create a new job posting with details, including title, description, industry, average salary, and location.

    Endpoint: http://localhost:5001/create/jobPost

    Example body:
        { 
        "title": "Machine Learning Engineer",
        "industry": "Agricultural Tech",
        "description": "Designing and developing machine learning systems, implementing appropriate ML algorithms, and conducting experiments to predict crop yields",
        "average_salary": 130000,
        "company_name": "Plantify", 
        "location": "Potlach, ID"
        }

    Example response:
        {
        "job_id": 101,
        "message": "Job post created successfully"
        }
    """
    if request.method == 'GET':
        return jsonify({
            "message": "This endpoint creates a new job posting. Send a POST request with job details in the body to create a new job post. Required fields are 'title', 'industry', and 'company_name'. Any additional fields provided will be included in the job post."
        }), 200

    try:
        # Select the collections
        jobs_collection = db.jobs
        industries_collection = db.industries
        
        # Get the data from the request
        data = request.json
        
        # Validate that required fields are present 
        if not data.get('title') or not data.get('industry') or not data.get('company_name'):
            return jsonify({'error': 'Title, industry, and company name are required fields'}), 400
        
        # Prepare the job post with all provided fields
        job_post = {key: value for key, value in data.items()}
        job_post['created_at'] = datetime.utcnow()

        # Generate a unique job_id
        job_post['job_id'] = utils.generate_unique_job_id(jobs_collection)

        # Check if the industry exists in the industries collection
        industry = industries_collection.find_one({"industry_name": data['industry'].capitalize()})
        
        new_industry_added = False
        if not industry:
            # Add the new industry to the industries collection
            industries_collection.insert_one({"industry_name": data['industry'].capitalize()})
            new_industry_added = True

        # Insert the job post into the database
        result = jobs_collection.insert_one(job_post)

        if result.inserted_id:
            response = {
                'message': 'Job post created successfully', 
                'job_id': job_post['job_id']
            }
            # Provide additional information if a new industry was added so user knows they can add more information about the industry if they want 
            if new_industry_added:
                response['additional_info'] = f"A new industry '{data['industry']}' was added to the database. You can use the add_industry_info function to provide more details about it if you want."
            return jsonify(response), 201
        else:
            return jsonify({'error': 'Failed to create job post'}), 500 # Internal server error

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500 # Internal server error



# Additional function so user can add more industry details if they want, trying to mimic dynamic nature of modern job market 
@app.route("/add/industry_info", methods=['POST', 'GET'])
def add_industry_info():
    """
    Add or update industry information in the database.

    Endpoint: http://localhost:5001/add/industry

    Example body:
    {
        "industry_name": "Prompt Engineering",
        "growth_rates": [0.03, 0.06, 0.1, 0.04, 0.04],
        "industry_skills": ["Problem Solving", "Communication", "Analytics"],
        "top_companies": ["Prompt Engineering Agency"],
        "trends": ["Generative AI", "Prompt Engineering Tools"]
    }

    Example response:
    {
        "message": "Industry information added/updated successfully",
        "industry_name": "Prompt Engineering"
    }
    """
    if request.method == 'GET':
        return jsonify({
            "message": "This endpoint adds or updates industry information. Send a POST request with industry details in the body. 'industry_name' is required, all other fields are optional and will be added or updated as provided."
        }), 200

    try:
        # Select the industries collection
        industries_collection = db.industries
        
        # Get the data from the request
        data = request.json
        
        # Validate that industry_name is present
        if not data.get('industry_name'):
            return jsonify({'error': 'industry_name is a required field'}), 400 # Bad request
        
        # Prepare the industry document
        industry_doc = {key: value for key, value in data.items() if key != 'industry_name'}
        
        # Update the industry information 
        result = industries_collection.update_one(
            {"industry_name": data['industry_name']},
            {"$set": industry_doc},
            upsert=True
        )

        if result.modified_count > 0 or result.upserted_id:
            action = "updated" if result.modified_count > 0 else "added"
            return jsonify({
                'message': f'Industry information {action} successfully',
                'industry_name': data['industry_name']
            }), 200
        else:
            return jsonify({'error': 'Failed to add/update industry information'}), 500 # Internal server error

    except Exception as e:
        return jsonify({'error': 'An unexpected error occurred', 'details': str(e)}), 500 # Internal server error



@app.route("/search_by_job_id/<job_id>", methods=['GET'])
def view_job_details(job_id):
    """ 
    This endpoint allows users to search for a specific job posting using its unique job ID.
    It returns the full details of the job if found, or an error message if not found.

    Endpoint: http://localhost:5001/search_by_job_id/<job_id>

    Optional body: User can specify specific fields they are intereted in 
    {
        "fields": ["title", "description", "average_salary"]
    }

    Example response (for the job with job_id 12):
    [
        {
            "average_salary": 98866,
            "description": "This position requires close collaboration..",
            "title": "Financial Data Scientist"
        }
    ]
    """
    try:
        # Select the jobs collection
        jobs_collection = db.jobs

        # Convert job_id to integer
        job_id = int(job_id)

        projection = {'_id': 0}
        
        # Check if the request has a body and if it's JSON
        if request.content_length:
            if request.is_json:
                print("inside second if")
                body = request.json
                if body and 'fields' in body:
                    for field in body['fields']:
                        projection[field] = 1
            else:
                return jsonify({"error": "Invalid JSON in request body"}), 400

        # Find the job by job_id
        job = jobs_collection.find({"job_id": job_id}, projection)

        if job:
            return jsonify(list(job)), 200 
        else:
            return jsonify({"error": "Job not found"}), 404 # Not found

    except ValueError:
        return jsonify({"error": "Invalid job_id format"}), 400 # Bad request
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500 # Internal server error



@app.route("/update_by_job_title", methods=['GET', 'POST'])
def update_job_details():
    try:
        # Select the jobs collection
        jobs_collection = db.jobs

        # If it's a GET request, provide instructions
        if request.method == 'GET':
            return jsonify({
                "message": "To update a job, follow these steps:",
                "instructions": {
                    "1": "Send a POST request to this endpoint with the job title, at least one other field, and update data",
                    "2": "If job(s) are found, you'll receive a confirmation request",
                    "3": "Send another POST request with 'confirm_update' to finalize the update"
                },
                "example": {
                    "first_request": {
                       "title": "<job title>",
                       "job_id": "<job_id>", 
                       "company_name": "<company name>",  
                       "employment_type": "<employment type>",  
                       "update": {
                           "description": "New description",
                           "average_salary": 75000,
                           "location": "New location"
                       }
                    },
                    "confirmation_request": {
                        "title": "<job title>",
                        "job_id": "<job_id>",  
                        "company_name": "<company name>", 
                        "employment_type": "<employment type>", 
                        "update": {
                            "description": "New description",
                            "average_salary": 75000,
                            "location": "New location"
                        },
                        "confirm_update": "true"
                    }
                }
            }), 200
        
        elif request.method == 'POST':
            job_title = request.json.get('title')
            job_id = request.json.get('job_id')
            company_name = request.json.get('company_name')
            employment_type = request.json.get('employment_type')
            
            # Validate input 
            if not job_title:
                return jsonify({"error": "Job title is required"}), 400

            # Check if at least one additional field is provided
            additional_fields = [job_id, company_name, employment_type]
            if not any(additional_fields):
                return jsonify({"error": "At least one additional field (job_id, company_name, or employment_type) is required"}), 400

            # Build the query
            query = {"title": job_title}
            if job_id:
                query["job_id"] = int(job_id)
            if company_name:
                query["company_name"] = company_name
            if employment_type:
                query["employment_type"] = employment_type
            
            # Find all jobs matching the query
            jobs = list(jobs_collection.find(query))

            if not jobs:
                return jsonify({"error": "No jobs found matching the criteria"}), 404
            
            # If it's the first POST request, ask for confirmation
            if 'confirm_update' not in request.json:
                return jsonify({
                    "message": f"Found {len(jobs)} job(s) matching the criteria. Are you sure you want to update these job(s)?",
                    "job_count": len(jobs),
                    "matching_job(s)": [
                        {
                            "title": job.get('title', 'N/A'),
                            "company_name": job.get('company_name', 'N/A'),
                            "employment_type": job.get('employment_type', 'N/A'),
                            "description": job.get('description', 'N/A')
                        } for job in jobs
                    ],
                    "instructions": "To confirm update, send another POST request with 'confirm_update:true' and the same search criteria"
                }), 200

            elif request.json.get('confirm_update') == 'true':
                update_data = request.json.get('update', {})
                
                # Check if job_id is in the update data
                if 'job_id' in update_data:
                    return jsonify({
                        "error": "The job_id field cannot be manually updated by users as it should remain unique.",
                        "message": "Please remove job_id from your update request and try again."
                    }), 400
                
                # Validate update data
                updatable_fields = ['description', 'average_salary', 'location']
                for field in update_data:
                    if field not in updatable_fields:
                        return jsonify({"error": f"Invalid update field: {field}"}), 400
                
                # Validate salary if provided
                if 'average_salary' in update_data:
                    try:
                        update_data['average_salary'] = float(update_data['average_salary'])
                    except ValueError:
                        return jsonify({"error": "Invalid salary format"}), 400
                
                # Update all jobs matching the query in the database
                result = jobs_collection.update_many(query, {"$set": update_data})
                
                if result.modified_count:
                    return jsonify({"message": f"Successfully updated {result.modified_count} job(s) matching the criteria", "updated_fields": list(update_data.keys())}), 200
                else:
                    return jsonify({"message": "No changes were made"}), 200
            else:
                return jsonify({"error": "Invalid confirmation value"}), 400
        
        # If the method is neither GET nor POST
        return jsonify({"error": "Invalid request method"}), 405
    
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500





@app.route('/delete_by_job_title', methods=['GET', 'POST'])
def delete_by_job_title():
    """ 
    This endpoint allows users to delete job titles by specifying the job title and at least one of the following fields: "job_id, company_name, employment_type".
    Additional parameters can be passed in for more precise targeting 

    Endpoint: http://localhost:5001/delete_by_job_title

    Required body:
        { 
        "title": "IT Consultant",
        < One additional field is required >
        }

    Optional additional fields (at least one of these is required, but any field can be passed in):
        "job_id": 1,
        "company_name": "DataDive Analytics",
        "employment_type": "Full-time"

    Example response:
    {
        "message": "Successfully deleted 1 job(s) matching the criteria"
    }
    
    """
    try:

        # If it's a GET request, provide instructions
        if request.method == 'GET':
            return jsonify({
                "message": "To delete a job, follow these steps:",
                "instructions": {
                    "1": "Send a POST request to this endpoint with the job title and optional parameters",
                    "2": "If job(s) are found, you'll receive a confirmation request",
                    "3": "Send another POST request with 'confirm_delete' to finalize deletion"
                },
                "example": {
                    "first_request": {
                       "job_title": "<job title>",
                       "job_id": "<job_id>",  
                       "company": "<company name>",  
                       "employment_type": "<employment type>"  
                    },
                    "confirmation_request": {
                        "job_title": "<job title>",
                        "job_id": "<job_id>",  # Include if used in first request
                        "company": "<company name>",  # Include if used in first request
                        "employment_type": "<employment type>",  # Include if used in first request
                        "confirm_delete": "true"
                    }
                }
            }), 200


        elif request.method == 'POST':
            job_title = request.json.get('title')
            job_id = request.json.get('job_id')
            company = request.json.get('company')
            employment_type = request.json.get('employment_type')
            job_posting_url = request.json.get("job_posting_url")
            
            # Validate input needs to include one of the following: job_title, job_id, company_name, or employment_type
            if not job_title or not any([job_id, company, employment_type]):
                return jsonify({"error": "Job title and at least one additional field is required"}), 400

            # Select the jobs collection
            jobs_collection = db.jobs
            
            # Build the query
            query = {"title": job_title}
            if job_id:
                query["job_id"] = int(job_id)
            if company:
                query["company_name"] = company
            if employment_type:
                query["employment_type"] = employment_type
            if job_posting_url:
                query["job_posting_url"] = job_posting_url
            
            # Find all jobs matching the query
            jobs = list(jobs_collection.find(query))

            if not jobs:
                return jsonify({"error": "No jobs found matching the criteria"}), 404
            
            # If it's the first POST request, ask for confirmation
            if 'confirm_delete' not in request.json:
                return jsonify({
                    "message": f"Found {len(jobs)} job(s) matching the criteria. Are you sure you want to delete these job(s)?",
                    "job_count": len(jobs),
                    "sample_job": {
                        "title": jobs[0].get('title', 'N/A'),
                        "job_id": jobs[0].get('job_id', 'N/A'),
                        "company": jobs[0].get('company_name', 'N/A'),
                        "employment_type": jobs[0].get('employment_type', 'N/A'),
                        "description": jobs[0].get('description', 'N/A')
                    },
                    "instructions": "To confirm deletion, send another POST request with 'confirm_delete:true' and the same search criteria"
                }), 200
            
            # If it's the POST to confirm deletion
            elif request.json.get('confirm_delete') == 'true':
                # Delete all jobs matching the query from the database
                result = jobs_collection.delete_many(query)
                
                if result.deleted_count:
                    return jsonify({"message": f"Successfully deleted {result.deleted_count} job(s) matching the criteria"}), 200
                else:
                    return jsonify({"error": "Failed to delete jobs"}), 500
            else:
                return jsonify({"error": "Invalid confirmation value"}), 400
        
    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@app.route('/jobs_by_salary', methods=['GET'])
def get_jobs_by_salary():
    """ 
    This endpoint allows users to query jobs based on a salary range

    Endpoint: http://localhost:5001/jobs_by_salary

    Required body:
    { 
        "min_salary": 85247,
        "max_salary": 85248
    }

    Optional body:  User can specify specific fields they are intereted in 
    {
        "fields": ["title", "company_name", "average_salary"]
    }

    Example response:

    {
        "jobs": [
            {
                "average_salary": 85248,
                "company_name": "Nimbus Tech",
                "title": "Machine Learning Engineer"
            }
        ]
    }

    """
    try:
        min_salary = float(request.json.get('min_salary'))
        max_salary = float(request.json.get('max_salary'))
        fields = request.json.get('fields')

        # Validate salary min and max fields 
        if min_salary is None or max_salary is None:
            return jsonify({"error": "Both min_salary and max_salary must be provided"}), 400

        # Validate that min_salary is not greater than max_salary
        if min_salary > max_salary:
            return jsonify({"error": "min_salary cannot be greater than max_salary"}), 400

        # Select the jobs collection
        jobs_collection = db.jobs

        # Query jobs within the salary range
        query = {
            "$and": [
                {"average_salary": {"$gte": min_salary}},
                {"average_salary": {"$lte": max_salary}}
            ]
        }

        # Set up projection based on user-specified fields
        projection = {"_id": 0}
        if fields:
            for field in fields:
                projection[field] = 1
        
        jobs = list(jobs_collection.find(query, projection))

        if jobs:
            return jsonify({"jobs": jobs}), 200
        else:
            return jsonify({"message": "No jobs found in the specified salary range"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


@app.route('/jobs_by_experience', methods=['GET'])
def get_jobs_by_experience():
    """ 
    This endpoint allows users to retrieve job listings based on the specified experience level(s).

    Endpoint: http://localhost:5001/jobs_by_experience

    Required body:
    {
        "experience_level": "Senior Level"
    }
    OR
    {
        "experience_level": ["Entry Level", "Mid Level"]
    }

    Optional body: User can specify specific fields they are intereted in 
    {
        "fields": ["title", "company_name", "average_salary"]
    }

    Example response:
    {
    "jobs": [
        {
            "average_salary": 109817,
            "company_name": "AlphaTech Ventures",
            "title": "Healthcare Data Analyst"
        },
        {
            "average_salary": 141005,
            "company_name": "Pioneer Data Services",
            "title": "Bioinformatics Scientist"
        },
        ...
    }
    """

    try:
        experience_level_input = request.json.get('experience_level')
        fields = request.json.get('fields')

        if not experience_level_input:
            return jsonify({"error": "experience_level parameter must be provided"}), 400
        
        # Set up projection based on user-specified fields
        projection = {"_id": 0}

        # Handle both single string and list inputs
        if isinstance(experience_level_input, str):
            experience_levels = [experience_level_input]
        
        elif isinstance(experience_level_input, list):
            experience_levels = experience_level_input
            projection["experience_level"] = 1

        else:
            return jsonify({"error": "experience_level must be a string or a list of strings"}), 400

        levels = []
        for level in experience_levels:
            level = level.lower()
            if "entry" in level:
                levels.append("Entry Level")
            elif "mid" in level:
                levels.append("Mid Level")
            elif "senior" in level:
                levels.append("Senior Level")
            else:
                return jsonify({"message": f"{level} is not a valid experience level in the career hub. Valid options include Entry Level, Mid Level, and Senior Level"}), 404

        # Select the jobs collection
        jobs_collection = db.jobs

        # Query jobs with the specified experience level(s)
        query = {"experience_level": {"$in": levels}}
        
        # Set up projection based on user-specified fields
        if fields:
            for field in fields:
                projection[field] = 1
        
        jobs = list(jobs_collection.find(query, projection))

        if jobs:
            return jsonify({"jobs": jobs}), 200
        else:
            return jsonify({"message": f"No jobs found for experience level(s): {', '.join(levels)}"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500



@app.route('/top_companies_by_industry', methods=['GET'])
def get_top_companies_by_industry():
    """ 
    Fetch top companies in a given industry based on the number of job listings

    Endpoint: http://localhost:5001/top_companies_by_industry

    Required body:
    {
        "industry_name": "Finance"
    }

    Example response:
    {
        "top_companies": [
            {
                "company_name": "NexaCore Tech",
                "job_count": 4
            },
            {
                "company_name": "DataPulse Systems",
                "job_count": 4
            },
            ..., 

            {
                "company_name": "EagleEye Data",
                "job_count": 1
            }
        ]
    }
    """
    try:
        industry = request.json.get('industry_name')

        if not industry:
            return jsonify({"error": "industry parameter must be provided"}), 400

        # Select the jobs collection
        jobs_collection = db.jobs

        # Aggregate pipeline to get top companies
        pipeline = [
            {"$match": {"industry_name": industry}},
            {"$group": {
                "_id": "$company_name",
                "job_count": {"$sum": 1}
            }},
            {"$sort": {"job_count": -1}},
            {"$project": {
                "_id": 0,
                "company_name": "$_id",
                "job_count": 1
            }}
        ]

        top_companies = list(jobs_collection.aggregate(pipeline))

        if top_companies:
            return jsonify({"top_companies": top_companies}), 200
        else:
            return jsonify({"message": f"No companies found for industry: {industry}"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500




@app.route('/industry_info', methods=['GET'])
def get_industry_info():
    """
    Fetch industry information based on industry name from the industries collection.

    Endpoint: http://localhost:5001/industry_info

    Required body:
    {
        "industry_name": "Tech"
    }

    Optional body:
    {
        "fields": ["growth_rates"]
    }

    Example response:
    {
        "industry_info": {
            "industry_name": "Consulting",
            "top_companies": [
                "Deloitte",
                "EY",
                "KPMG",
                "Accenture",
                "PwC"
                ], 
            "trends": [
                "Remote Work Consulting",
                "Digital Transformations",
                "Sustainable Business Models",
                "Cybersecurity Consulting",
                "AI Strategy"
                ]
        }
    }
    """
    try:
        industry_name = request.json.get('industry_name')
        fields = request.json.get('fields')

        if not industry_name:
            return jsonify({"error": "industry_name parameter must be provided"}), 400

        # Select the industries collection
        industries_collection = db.industries

        # Set up projection based on user-specified fields
        projection = {"_id": 0, "industry_name": 1, "top_companies": 1, "trends": 1}
        if fields:
            for field in fields:
                projection[field] = 1

        # Query the industry
        industry = industries_collection.find_one({"industry_name": industry_name}, projection)

        if industry:
            return jsonify({"industry_info": industry}), 200
        else:
            return jsonify({"message": f"No information found for industry: {industry_name}"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500





@app.route('/company_info', methods=['GET'])
def get_company_info():
    """
    Fetch company information based on company name from the companies collection.

    Endpoint: http://localhost:5001/company_info

    Required body:
    {
        "company_name": "DataDive Analytics"
    }

    Optional body:
    {
        "fields": ["company_id", "size", "industry_name"]
    }

    Example response:
    {
        "company_info": {
            "company_id": "TechCorp",
            "size": "1-10",
            "industry_name": "Consulting"
        }
    }
    """
    try:
        company_name = request.json.get('company_name')
        fields = request.json.get('fields')

        if not company_name:
            return jsonify({"error": "company_name parameter must be provided"}), 400

        # Select the companies collection
        companies_collection = db.companies

        # Set up projection based on user-specified fields
        projection = {"_id": 0, "name": 1, "industry_name": 1}
        if fields:
            for field in fields:
                projection[field] = 1

        # Query the company
        company = companies_collection.find_one({"name": company_name}, projection)

        if company:
            return jsonify({"company_info": company}), 200
        else:
            return jsonify({"message": f"No information found for company: {company_name}"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500



@app.route("/search_by_industry/", methods=['GET'])
def search_jobs_by_industry():
    """ 
    This endpoint allows users to search for job postings in a specific industry.
    It returns a list of jobs in the specified industry or an error message if none are found.

    Endpoint: http://localhost:5001/search_by_industry/

    Required body:
    {
        "industry_name": "Finance"
    }

    Optional body: User can specify specific fields they are interested in 
    {
        "fields": ["title", "company_name", "average_salary"]
    }

    Example response:
    {
        "jobs": [
            {
                "title": "Data Scientist",
                "company_name": "TechCorp",
                "average_salary": 95000
            },
            {
                "title": "Software Engineer",
                "company_name": "InnoSoft",
                "average_salary": 90000
            }
        ],
        "total_jobs": 2
    }
    """
    try:
        # Select the jobs collection
        jobs_collection = db.jobs

        # Get the industry name from the request body
        industry_name = request.json.get('industry_name')

        # Validate that industry_name is provided
        if not industry_name:
            return jsonify({"error": "industry_name parameter must be provided in the request body"}), 400

        projection = {'_id': 0}
        
        # Check if the request has fields specified in the body
        if 'fields' in request.json:
            for field in request.json['fields']:
                projection[field] = 1
        else:
            # Default fields if none specified
            projection = {'_id': 0, 'title': 1, 'company_name': 1, 'average_salary': 1}

        # Find jobs by industry name
        jobs = list(jobs_collection.find({"industry_name": industry_name}, projection))

        if jobs:
            return jsonify({
                "jobs": jobs,
                "total_jobs": len(jobs)
            }), 200
        else:
            return jsonify({"error": f"No jobs found in the {industry_name} industry"}), 404

    except Exception as e:
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

