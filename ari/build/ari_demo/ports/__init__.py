"""Ports — FROZEN wave-0 contract (hexagonal boundary, ADR 0001/0003).

Every port method takes a RequestContext (or a ModelRequest that carries one):
no adapter is callable without an identity. Adapters implement these Protocols
in their own directories; the core depends only on the Protocol.
"""
from .ports import (
    ActionPort,
    ClassifierPort,
    DocsPort,
    ModelPort,
    OmniPort,
    TicketPort,
)

__all__ = [
    "ModelPort",
    "ClassifierPort",
    "OmniPort",
    "DocsPort",
    "TicketPort",
    "ActionPort",
]
