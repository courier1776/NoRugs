from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Any

from norugs_scraper.database import Database
from norugs_scraper.http import ApiClient
from norugs_scraper.settings import Settings


class GitHubProvider:
    SOURCE_NAME = "GitHub"
    BASE_URL = "https://api.github.com"

    # Each repo costs 4 requests (repo info, commits, contributors, closed
    # issues). GitHub's unauthenticated limit is 60 requests/hour, so with
    # the default github_max_repos_per_run=10 this uses at most 40 of that
    # budget per run, leaving headroom for retries/other calls.
    REQUESTS_PER_REPO = 4

    def __init__(self, settings: Settings, http: ApiClient, db: Database) -> None:
        self.settings = settings
        self.http = http
        self.db = db

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"
        return headers

    def _seconds_since_last_run(self) -> float | None:
        with self.db.connect() as conn:
            last = self.db.last_completed_at(conn, self.SOURCE_NAME)
        if last is None:
            return None
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        return (datetime.now(timezone.utc) - last).total_seconds()

    def collect(self, repositories: list[dict[str, str]]) -> int:
        if not repositories:
            return 0

        # Without a token, GitHub allows only 60 unauthenticated requests an
        # hour. Refreshing every configured repo on every collection cycle
        # would blow through that instantly once more than a couple of repos
        # are tracked. Instead, run at most once per
        # github_refresh_interval_seconds, and even then only touch a
        # rotating batch of github_max_repos_per_run repos, so the whole
        # list eventually gets refreshed without ever exceeding the budget.
        elapsed = self._seconds_since_last_run()
        if elapsed is not None and elapsed < self.settings.github_refresh_interval_seconds:
            return 0

        batch_size = self.settings.github_max_repos_per_run
        total_batches = max(1, math.ceil(len(repositories) / batch_size))
        # Deterministic, stateless rotation: which batch runs is derived from
        # wall-clock time, so successive eligible runs naturally cycle
        # through the whole repository list instead of always refreshing
        # just the first N repos.
        batch_index = int(
            datetime.now(timezone.utc).timestamp() // self.settings.github_refresh_interval_seconds
        ) % total_batches
        batch = repositories[batch_index * batch_size : batch_index * batch_size + batch_size]

        count = 0
        for item in batch:
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
                with conn.transaction():
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
                        skip_no_crypto = True
                    else:
                        skip_no_crypto = False
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
                if skip_no_crypto:
                    self.db.finish_run(
                        conn,
                        run_id,
                        "PARTIAL",
                        found=1,
                        error="Cryptocurrency must be loaded from CoinGecko first",
                    )
                    return 0
                self.db.finish_run(conn, run_id, "SUCCESS", found=1, inserted=1)
                return 1
            except Exception as exc:
                self.db.finish_run(conn, run_id, "FAILED", error=str(exc))
                raise
