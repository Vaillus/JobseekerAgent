import json
from pathlib import Path
from typing import List

import sys
# print(">>> MON SYS.PATH ACTUEL:", sys.path) # Ligne de diagnostic

from jobseeker_agent.utils.paths import get_linkedin_keywords_path


class QueryBuilder:
    def __init__(self):
        self.keywords_dir = get_linkedin_keywords_path()
        self._load_keywords()

    def _load_keywords(self) -> None:
        self.main_jobtitle = self._read_json("main_jobtitle.json")
        self.main_fields = self._read_json("main_fields.json")
        self.secondary_jobtitle = self._read_json("secondary_jobtitle.json")
        self.blacklist = self._read_json("blacklist.json")

    def _read_json(self, filename: str) -> List[str]:
        with open(self.keywords_dir / filename, "r") as f:
            return json.load(f)

    def _format_with_or(self, keywords: List[str]) -> str:
        return f'({" OR ".join([f'"{kw}"' for kw in keywords])})'

    def build_primary_query(self) -> str:
        main_jobtitle_str = self._format_with_or(self.main_jobtitle)
        main_fields_str = self._format_with_or(self.main_fields)
        blacklist_str = self._format_with_or(self.blacklist)
        return f"{main_jobtitle_str} AND {main_fields_str} NOT {blacklist_str}"

    def build_secondary_query(self) -> str:
        secondary_jobtitle_str = self._format_with_or(self.secondary_jobtitle)
        blacklist_str = self._format_with_or(self.blacklist)
        return f"{secondary_jobtitle_str} NOT {blacklist_str}"


if __name__ == "__main__":
    # Assuming the script is run from the root of the project
    builder = QueryBuilder()

    primary_query = builder.build_primary_query()
    secondary_query = builder.build_secondary_query()

    print("Primary Query:")
    print(primary_query)
    print("\nSecondary Query:")
    print(secondary_query)
