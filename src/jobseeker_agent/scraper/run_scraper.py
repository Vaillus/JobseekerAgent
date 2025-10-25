from jobseeker_agent.scraper.linkedin_scraper import LinkedInJobsScraper
from jobseeker_agent.scraper.linkedin_query import QueryBuilder


def run_scraping(max_time="day"):
    """
    Run the scraping process with all configured locations and queries.
    
    Args:
        max_time: Time horizon for job postings ("day" or "week")
        
    Returns:
        Total number of new jobs added
    """
    builder = QueryBuilder()

    requests = [
        {"location": "Sidney, Australia", "remote_type": "any"},
        {"location": "Australia", "remote_type": "remote"},
        {"location": "Paris, France", "remote_type": "any"},
        {"location": "France", "remote_type": "remote"},
        {"location": "Germany", "remote_type": "remote"},
        {"location": "Amsterdam, Netherlands", "remote_type": "any"},
        {"location": "Netherlands", "remote_type": "remote"},
    ]
    queries = [builder.build_primary_query(), builder.build_secondary_query()]
    max_jobs = 100
    scraper = LinkedInJobsScraper()
    
    total_new_jobs = 0
    
    for request in requests:
        for query in queries:
            params = {
                "keywords": query,
                "location": request["location"],
                "max_jobs": max_jobs,
                "remote_type": request["remote_type"],
                "max_time": max_time,
            }
            new_jobs_added = scraper.scrape_jobs(**params)
            total_new_jobs += new_jobs_added
            print(f"Finished scraping {request['location']}. Added {new_jobs_added} new jobs.")
    
    print(f"Total: {total_new_jobs} new jobs added.")
    return total_new_jobs


def main():
    """Main entry point for command-line usage."""
    max_time = "day"
    run_scraping(max_time)


if __name__ == "__main__":
    main()
