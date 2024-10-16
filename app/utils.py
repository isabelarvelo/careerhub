"""This module will encode and parse the query string params."""

from urllib.parse import parse_qs


def parse_query_params(query_string):
    """
    Function to parse the query parameter string.
    """
    # Parse the query param string
    query_params = dict(parse_qs(query_string))
    # Get the value from the list
    query_params = {k.decode(): v[0].decode() for k, v in query_params.items()}
    return query_params


def generate_unique_job_id(jobs_collection):
    """
    Generate a unique job_id for a new job posting.

    Returns:
    int: A unique job_id
    """
    # Find the highest existing job_id
    highest_job = jobs_collection.find_one(
        {},
        sort=[("job_id", -1)],
        projection={"job_id": 1}
    )
    
    # If jobs exist, increment the highest job_id
    new_job_id = highest_job['job_id'] + 1

    return new_job_id
