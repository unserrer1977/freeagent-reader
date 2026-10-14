import re

import httpx
from pydantic import BaseModel
from typing import Optional

from src.api.config import settings


class FreeAgentResult(BaseModel):
    success: bool
    data: Optional[dict] = None
    message: Optional[str] = None
    error: Optional[str] = None


class FreeAgentClient:
    """Read-only client for the FreeAgent API v2."""

    def __init__(self, config, access_token: str, is_sandbox: bool, company_name: Optional[str] = None):
        self.base_url = "https://api.sandbox.freeagent.com/v2" if is_sandbox else "https://api.freeagent.com/v2"
        self.access_token = access_token
        self.is_sandbox = is_sandbox
        self.company_name = company_name

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Accept": "application/json",
            "User-Agent": "freeagent-reader/1.0",
        }

    def _get(self, path: str, params: Optional[dict] = None) -> FreeAgentResult:
        url = f"{self.base_url}{path}"
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, headers=self._headers(), params=params)
                resp.raise_for_status()
                return FreeAgentResult(success=True, data=resp.json())
        except httpx.HTTPStatusError as e:
            body = e.response.text[:500] if e.response else str(e)
            return FreeAgentResult(success=False, error=f"HTTP {e.response.status_code}: {body}")
        except httpx.HTTPError as e:
            return FreeAgentResult(success=False, error=str(e))

    # ---- Entity endpoints ----

    def _list(self, endpoint: str, params: Optional[dict] = None) -> FreeAgentResult:
        return self._get(f"/v2/{endpoint}", params=params)

    def get_company(self) -> FreeAgentResult:
        return self._get("/v2/company")

    def get_accounts(self) -> FreeAgentResult:
        return self._list("accounts")

    def get_transactions(self, params: Optional[dict] = None) -> FreeAgentResult:
        return self._list("transactions", params=params)

    def get_invoices(self, params: Optional[dict] = None) -> FreeAgentResult:
        return self._list("invoices", params=params)

    def get_bank_accounts(self) -> FreeAgentResult:
        return self._list("bank_accounts")

    def get_bank_transactions(self, params: Optional[dict] = None) -> FreeAgentResult:
        return self._list("bank_transactions", params=params)

    def get_contacts(self, params: Optional[dict] = None) -> FreeAgentResult:
        return self._list("contacts", params=params)

    def get_projects(self) -> FreeAgentResult:
        return self._list("projects")

    def get_categories(self) -> FreeAgentResult:
        return self._list("categories")

    def get_tags(self) -> FreeAgentResult:
        return self._list("tags")

    def get_budgets(self) -> FreeAgentResult:
        return self._list("budgets")

    def get_weekly_metrics(self) -> FreeAgentResult:
        return self._list("weekly_metrics")

    def get_period(self) -> FreeAgentResult:
        return self._list("period")

    # ---- Query engine ----

    def answer_query(self, query: str) -> FreeAgentResult:
        q = query.lower().strip()
        # Strip common prefixes like "what", "show", "list", "tell me about"
        q = re.sub(r"^(what|show|list|tell me about|can you show|please )", "", q)

        # Entity matching
        entity_map = {
            "company": ("company", {}),
            "accounts": ("accounts", {}),
            "account": ("accounts", {}),
            "transactions": ("transactions", {}),
            "transaction": ("transactions", {}),
            "invoices": ("invoices", {}),
            "invoice": ("invoices", {}),
            "bank accounts": ("bank_accounts", {}),
            "bank account": ("bank_accounts", {}),
            "contacts": ("contacts", {}),
            "contact": ("contacts", {}),
            "projects": ("projects", {}),
            "project": ("projects", {}),
            "categories": ("categories", {}),
            "category": ("categories", {}),
            "tags": ("tags", {}),
            "tag": ("tags", {}),
            "budgets": ("budgets", {}),
            "budget": ("budgets", {}),
            "weekly metrics": ("weekly_metrics", {}),
            "weekly metric": ("weekly_metrics", {}),
            "period": ("period", {}),
            "bank transactions": ("bank_transactions", {}),
            "bank transaction": ("bank_transactions", {}),
        }

        chosen = None
        for key in entity_map:
            if key in q:
                chosen = entity_map[key]
                break

        if chosen is None:
            # Try to list everything
            return self._list_all(q)

        endpoint, params = chosen

        # Apply filters
        if "invoice" in endpoint:
            if "overdue" in q or "past due" in q:
                params["view"] = "overdue"
            elif "paid" in q or "paid or credited" in q or "settled" in q:
                params["view"] = "paid_or_credited"
            elif "open" in q or "unpaid" in q or "outstanding" in q or "due" in q:
                params["view"] = "open_or_overdue"

        if endpoint == "transactions":
            if "paid" in q or "paid expense" in q:
                params["view"] = "paid"
            elif "outstanding" in q or "pending" in q or "unpaid" in q:
                params["view"] = "outstanding"

        # Pagination
        if params is None:
            params = {}
        params["per_page"] = params.get("per_page", 50)

        return self._list(endpoint, params=params)

    def _list_all(self, query: str) -> FreeAgentResult:
        results = {}
        sections = [
            ("company", self.get_company),
            ("accounts", self.get_accounts),
            ("transactions", self.get_transactions),
            ("invoices", self.get_invoices),
            ("bank_accounts", self.get_bank_accounts),
            ("bank_transactions", self.get_bank_transactions),
            ("contacts", self.get_contacts),
            ("projects", self.get_projects),
            ("categories", self.get_categories),
            ("tags", self.get_tags),
            ("budgets", self.get_budgets),
            ("weekly_metrics", self.get_weekly_metrics),
            ("period", self.get_period),
        ]
        for name, fn in sections:
            res = fn()
            if res.success and res.data:
                results[name] = res.data
        return FreeAgentResult(
            success=True,
            data={"summary": "Here's everything:" + (" " + query if query else ""), "results": results},
        )
