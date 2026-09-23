"""External tools package for the LangGraph agent (Part 2)."""

from agent.tools.incidents import lookup_support_ticket
from agent.tools.inventory import lookup_inventory_stock
from agent.tools.routing import classify_intent, extract_product_query, extract_ticket_id

__all__ = [
    "classify_intent",
    "extract_ticket_id",
    "extract_product_query",
    "lookup_support_ticket",
    "lookup_inventory_stock",
]
