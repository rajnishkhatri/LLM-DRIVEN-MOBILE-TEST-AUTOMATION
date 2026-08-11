"""Check clusters: one function per CHK id, registered in registry.CHECKS.

A check consumes the loaded Context and returns Finding tuples
(artifact_label, json_pointer, detail). It never touches filesystem paths
except through the context root (CHK-REFS), keeping verdicts path-independent.
"""
