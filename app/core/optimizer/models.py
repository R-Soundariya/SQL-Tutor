"""Data models for the Query Optimizer feature."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StaticFinding:
    """One deterministic, LLM-free issue found by static analysis."""

    category: str
    severity: str  # "info" | "warning" | "critical"
    message: str


@dataclass(frozen=True)
class OptimizationResult:
    """AI-generated rewrite and recommendations for a query."""

    rewritten_query: str
    performance_notes: str
    index_recommendations: tuple[str, ...]
    estimated_impact: str
