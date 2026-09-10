from __future__ import annotations

from datetime import datetime
from urllib.parse import quote

import httpx

from .models import PullRequest, RepositoryConfig


class AzureDevOpsClient:
    def __init__(self, organization: str, pat: str, timeout: float = 30.0) -> None:
        self.organization = organization
        self.base_url = f"https://dev.azure.com/{quote(organization, safe='')}"
        self.client = httpx.Client(
            auth=("", pat),
            headers={"Accept": "application/json"},
            timeout=timeout,
        )

    def __enter__(self) -> "AzureDevOpsClient":
        return self

    def __exit__(self, *_: object) -> None:
        self.client.close()

    def _get(self, url: str, params: dict[str, str | int] | None = None) -> dict:
        response = self.client.get(url, params=params)
        if response.status_code in (401, 403):
            raise RuntimeError("Azure DevOps rechazó el PAT; verifica que tenga permiso de lectura de código")
        response.raise_for_status()
        return response.json()

    def authenticated_user_id(self) -> str:
        data = self._get(
            f"{self.base_url}/_apis/connectionData",
            {"connectOptions": 1, "lastChangeId": -1, "lastChangeId64": -1},
        )
        user_id = (data.get("authenticatedUser") or {}).get("id")
        if not user_id:
            raise RuntimeError("No fue posible identificar al usuario autenticado")
        return str(user_id)

    def list_pull_requests(
        self,
        repo: RepositoryConfig,
        creator_id: str,
        status: str,
        since: datetime | None = None,
    ) -> list[PullRequest]:
        project = quote(repo.project, safe="")
        repository = quote(repo.repository, safe="")
        url = f"{self.base_url}/{project}/_apis/git/repositories/{repository}/pullrequests"
        params: dict[str, str | int] = {
            "searchCriteria.creatorId": creator_id,
            "searchCriteria.status": status,
            "$top": 100,
            "api-version": "7.1",
        }
        if since and status == "completed":
            params["searchCriteria.minTime"] = since.isoformat()
            params["searchCriteria.queryTimeRangeType"] = "Closed"

        data = self._get(url, params)
        return [self._to_pull_request(item, repo) for item in data.get("value", [])]

    def changed_files(self, pr: PullRequest) -> list[str]:
        project = quote(pr.project, safe="")
        repository = quote(pr.repository, safe="")
        root = f"{self.base_url}/{project}/_apis/git/repositories/{repository}/pullRequests/{pr.id}"
        iterations = self._get(f"{root}/iterations", {"api-version": "7.1"}).get("value", [])
        if not iterations:
            return []
        iteration_id = max(int(item["id"]) for item in iterations)
        data = self._get(
            f"{root}/iterations/{iteration_id}/changes",
            {"$compareTo": 0, "$top": 2000, "api-version": "7.1"},
        )
        paths = {
            str(change.get("item", {}).get("path"))
            for change in data.get("changeEntries", [])
            if change.get("item", {}).get("path")
        }
        return sorted(paths)

    def _to_pull_request(self, data: dict, repo: RepositoryConfig) -> PullRequest:
        pr_id = int(data["pullRequestId"])
        source = _strip_ref(str(data.get("sourceRefName", "")))
        target = _strip_ref(str(data.get("targetRefName", "")))
        web_url = (
            f"{self.base_url}/{quote(repo.project, safe='')}/_git/"
            f"{quote(repo.repository, safe='')}/pullrequest/{pr_id}"
        )
        closed = data.get("closedDate")
        return PullRequest(
            id=pr_id,
            title=str(data.get("title", "")),
            project=repo.project,
            repository=repo.repository,
            source_branch=source,
            target_branch=target,
            status=str(data.get("status", "")),
            url=web_url,
            merge_commit=(data.get("lastMergeCommit") or {}).get("commitId"),
            closed_date=datetime.fromisoformat(closed.replace("Z", "+00:00")) if closed else None,
        )


def _strip_ref(value: str) -> str:
    return value.removeprefix("refs/heads/")

