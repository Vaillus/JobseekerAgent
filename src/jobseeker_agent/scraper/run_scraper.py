from jobseeker_agent.scraper.linkedin_scraper import LinkedInJobsScraper
from jobseeker_agent.scraper.linkedin_query import QueryBuilder
from jobseeker_agent.utils.paths import load_scraping_destinations


def run_scraping(max_time="day", destinations_config=None):
    """
    Run the scraping process with all configured locations and queries.
    
    Args:
        max_time: Time horizon for job postings ("day", "week", "month" or int for N days)
        destinations_config: Optional list of destinations dicts with keys
            {"location": str, "remote_type": str, "enabled": bool}
        
    Returns:
        Total number of new jobs added
    """
    builder = QueryBuilder()

    # Load destinations from config if not provided
    if destinations_config is None:
        destinations_config = load_scraping_destinations()

    # Fallback defaults if config is empty
    if not destinations_config:
        destinations_config = [
            {"location": "Sidney, Australia", "remote_type": "any", "enabled": True},
            {"location": "Australia", "remote_type": "remote", "enabled": True},
            {"location": "Paris, France", "remote_type": "any", "enabled": True},
            {"location": "France", "remote_type": "remote", "enabled": True},
            {"location": "Germany", "remote_type": "remote", "enabled": True},
            {"location": "Amsterdam, Netherlands", "remote_type": "any", "enabled": True},
            {"location": "Netherlands", "remote_type": "remote", "enabled": True},
        ]

    primary_query = builder.build_primary_query()
    secondary_query = builder.build_secondary_query()
    max_jobs = 100
    scraper = LinkedInJobsScraper()
    
    total_new_jobs = 0
    for dest in destinations_config:
        if not dest.get("enabled", True):
            continue

        # Run primary query
        params_primary = {
            "keywords": primary_query,
            "location": dest["location"],
            "max_jobs": max_jobs,
            "remote_type": dest["remote_type"],
            "max_time": max_time,
        }
        new_jobs_added = scraper.scrape_jobs(**params_primary)
        total_new_jobs += new_jobs_added
        print(f"Finished scraping {dest['location']} (primary). Added {new_jobs_added} new jobs.")

        # Run secondary query
        params_secondary = {
            "keywords": secondary_query,
            "location": dest["location"],
            "max_jobs": max_jobs,
            "remote_type": dest["remote_type"],
            "max_time": max_time,
        }
        new_jobs_added = scraper.scrape_jobs(**params_secondary)
        total_new_jobs += new_jobs_added
        print(f"Finished scraping {dest['location']} (secondary). Added {new_jobs_added} new jobs.")
    
    print(f"Total: {total_new_jobs} new jobs added.")
    return total_new_jobs


def main():
    """Main entry point for command-line usage."""
    max_time = "day"
    run_scraping(max_time=max_time)


if __name__ == "__main__":
    main()
