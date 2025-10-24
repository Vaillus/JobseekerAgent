from jobseeker_agent.scraper.linkedin_scraper import LinkedInJobsScraper
from jobseeker_agent.scraper.linkedin_query import QueryBuilder


def main():
    builder = QueryBuilder()
    # query = builder.build_secondary_query()
    query = builder.build_primary_query()

    requests = [
        {"location": "Sidney, Australia", "remote_type": "any"},
        {"location": "Australia", "remote_type": "remote"},
        {"location": "Paris, France", "remote_type": "any"},
        {"location": "France", "remote_type": "remote"},
        {"location": "Germany", "remote_type": "remote"},
        {"location": "Amsterdam, Netherlands", "remote_type": "any"},
        {"location": "Netherlands", "remote_type": "remote"},
        # {
        #     "location": "California, USA",
        #     "remote_type": "remote"
        # }
    ]
    queries = [builder.build_primary_query(), builder.build_secondary_query()]
    max_jobs = 100
    max_time = "day"
    scraper = LinkedInJobsScraper()
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
            print(f"Finished scraping. Added {new_jobs_added} new jobs.")


if __name__ == "__main__":
    main()
