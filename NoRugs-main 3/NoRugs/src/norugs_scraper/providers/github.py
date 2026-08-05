from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from norugs_scraper.database import Database
from norugs_scraper.http import ApiClient
from norugs_scraper.settings import Settings


class GitHubProvider:
    SOURCE_NAME = "GitHub"
    BASE_URL = "https://api.github.com"

    def __init__(self, settings: Settings, http: ApiClient, db: Database) -> None:
        self.settings = settings
        self.http = http
        self.db = db

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        return headers

    def collect(self, repositories: list[dict[str, str]]) -> int:
        count = 0
        for item in repositories:
            count += self._collect_repo(item)
        return count

    def _collect_repo(self, item: dict[str, str]) -> int:
        owner, repo = item["owner"], item["repo"]
        repo_url = f"{self.BASE_URL}/repos/{owner}/{repo}"
        repo_data = self.http.get_json(repo_url, headers=self._headers())
        if not isinstance(repo_data, dict):
            raise RuntimeError("GitHub returned an unexpected repository response")

        since = datetime.now(timezone.utc) - timedelta(days=30)
        commits_url = f"{repo_url}/commits"
        commits = self.http.get_json(
            commits_url,
            params={"since": since.isoformat(), "per_page": 100},
            headers=self._headers(),
        )
        contributors_url = f"{repo_url}/contributors"
        contributors = self.http.get_json(
            contributors_url, params={"per_page": 100}, headers=self._headers()
        )
        issues_url = f"{repo_url}/issues"
        closed_issues = self.http.get_json(
            issues_url,
            params={"state": "closed", "since": since.isoformat(), "per_page": 100},
            headers=self._headers(),
        )

        observed_at = datetime.now(timezone.utc)
        combined: dict[str, Any] = {
            "repository": repo_data,
            "commits_30d": commits,
            "contributors": contributors,
            "closed_issues_30d": closed_issues,
        }
        with self.db.connect() as conn:
            source_id = self.db.source_id(conn, self.SOURCE_NAME)
            run_id = self.db.start_run(conn, source_id, item)
            try:
                self.db.save_raw(
                    conn,
                    run_id=run_id,
                    source_id=source_id,
                    external_id=f"{owner}/{repo}",
                    request_url=repo_url,
                    payload=combined,
                )
                crypto_id = self.db.crypto_id_by_external(conn, item["coingecko_id"])
                if crypto_id is None:
                    self.db.finish_run(
                        conn,
                        run_id,
                        "PARTIAL",
                        found=1,
                        error="Cryptocurrency must be loaded from CoinGecko first",
                    )
                    return 0
                commits_list = commits if isinstance(commits, list) else []
                contributors_list = contributors if isinstance(contributors, list) else []
                closed_list = closed_issues if isinstance(closed_issues, list) else []
                self.db.insert_developer_snapshot(
                    conn,
                    cryptocurrency_id=crypto_id,
                    source_id=source_id,
                    data={
                        "stars_count": repo_data.get("stargazers_count"),
                        "forks_count": repo_data.get("forks_count"),
                        "contributors_count": len(contributors_list),
                        "commits_30d": len(commits_list),
                        "issues_open": repo_data.get("open_issues_count"),
                        "issues_closed_30d": len(closed_list),
                        "last_commit_at": repo_data.get("pushed_at"),
                    },
                    observed_at=observed_at,
                )
                self.db.finish_run(conn, run_id, "SUCCESS", found=1, inserted=1)
                return 1
            except Exception as exc:
                self.db.finish_run(conn, run_id, "FAILED", error=str(exc))
                raise
