"""Domain layer — FROZEN wave-0 contract.

Pure types with no dependency on any adapter, port implementation, router or
model. Imports point inward: everything may import `domain`; `domain` imports
nothing from the rest of the package (enforced by the gate-12 structural test).
"""
