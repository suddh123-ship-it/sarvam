"""In-memory CRM store: customers, call records, and post-call status updates.

This is a demo-grade store (data lives in process memory, resets on restart).
It holds a few existing customers and the call records produced after each
telephonic conversation, so the dashboard has something to display.
"""
from datetime import datetime
from typing import Optional, Dict, List, Any
import re


# ── Customer status lifecycle ────────────────────────────────────────────────
# active          → known customer, no recent bot call
# call_completed  → bot handled a call and booking/query was resolved
# escalated       → call was handed off to a human supervisor
STATUS_ACTIVE = "active"
STATUS_CALL_COMPLETED = "call_completed"
STATUS_ESCALATED = "escalated"


def _normalize_phone(phone: str) -> str:
    """Reduce a phone number to its trailing digits for loose matching."""
    digits = re.sub(r"\D", "", phone or "")
    return digits[-10:] if len(digits) >= 10 else digits


class CRMStore:
    """Holds customers and call records for the dashboard."""

    def __init__(self):
        self.customers: Dict[str, Dict[str, Any]] = {}
        self.call_records: List[Dict[str, Any]] = []
        self._seed_dummy_customers()

    def _seed_dummy_customers(self):
        """Seed 3 existing customers so the dashboard is populated on startup."""
        seed = [
            {
                "id": "CUST-001",
                "name": "Rajesh Kumar",
                "phone": "+91 95153 50276",
                "vehicle_model": "Swift",
                "vehicle_year": "2022",
                "last_service_date": "2026-01-15",
                "status": STATUS_ACTIVE,
            },
            {
                "id": "CUST-002",
                "name": "Priya Sharma",
                "phone": "+91 99887 76655",
                "vehicle_model": "Creta",
                "vehicle_year": "2023",
                "last_service_date": "2026-03-02",
                "status": STATUS_ACTIVE,
            },
            {
                "id": "CUST-003",
                "name": "Amit Patel",
                "phone": "+91 91234 56789",
                "vehicle_model": "Nexon",
                "vehicle_year": "2021",
                "last_service_date": "2025-11-20",
                "status": STATUS_ACTIVE,
            },
        ]
        for c in seed:
            c["last_call_at"] = None
            c["last_call_summary"] = None
            self.customers[c["id"]] = c

    # ── Lookups ──────────────────────────────────────────────────────────────
    def find_customer_by_phone(self, phone: str) -> Optional[Dict[str, Any]]:
        """Match an incoming caller to an existing customer by phone digits."""
        target = _normalize_phone(phone)
        if not target:
            return None
        for cust in self.customers.values():
            if _normalize_phone(cust["phone"]) == target:
                return cust
        return None

    def list_customers(self) -> List[Dict[str, Any]]:
        return list(self.customers.values())

    def list_call_records(self) -> List[Dict[str, Any]]:
        """Most recent call first."""
        return sorted(self.call_records, key=lambda r: r["timestamp"], reverse=True)

    # ── Post-call update ─────────────────────────────────────────────────────
    def record_call(
        self,
        call_sid: str,
        phone: str,
        summary: str,
        intent: str,
        state: Dict[str, Any],
        escalated: bool,
    ) -> Dict[str, Any]:
        """Store a completed call and update the matched customer's status."""
        customer = self.find_customer_by_phone(phone)
        new_status = STATUS_ESCALATED if escalated else STATUS_CALL_COMPLETED
        now = datetime.now()

        record = {
            "call_sid": call_sid,
            "customer_id": customer["id"] if customer else None,
            "customer_name": customer["name"] if customer else "Unknown Caller",
            "phone": phone,
            "timestamp": now.isoformat(),
            "time_label": now.strftime("%d %b %Y, %I:%M %p"),
            "intent": intent,
            "vehicle_model": state.get("vehicle_model"),
            "service_type": state.get("service_type"),
            "preferred_date": state.get("preferred_date"),
            "turn_count": state.get("turn_count", 0),
            "escalated": escalated,
            "status": new_status,
            "summary": summary,
        }
        self.call_records.append(record)

        if customer:
            customer["status"] = new_status
            customer["last_call_at"] = record["time_label"]
            customer["last_call_summary"] = summary
            # Enrich the customer profile if the call surfaced fresh details.
            if state.get("vehicle_model"):
                customer["vehicle_model"] = state["vehicle_model"]

        return record

    def stats(self) -> Dict[str, int]:
        return {
            "total_customers": len(self.customers),
            "total_calls": len(self.call_records),
            "completed": sum(
                1 for r in self.call_records if r["status"] == STATUS_CALL_COMPLETED
            ),
            "escalated": sum(
                1 for r in self.call_records if r["status"] == STATUS_ESCALATED
            ),
        }


# Singleton instance
crm_store = CRMStore()
