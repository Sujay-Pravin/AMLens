from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class GraphMetrics:
    """
    Structured evidence produced by the transaction graph analyzer.
    """

    node_count: int
    edge_count: int
    num_components: int
    in_degree: Dict[str, int] = field(default_factory=dict)
    out_degree: Dict[str, int] = field(default_factory=dict)
    pagerank: Dict[str, float] = field(default_factory=dict)
    cycles: List[List[str]] = field(default_factory=list)
    hub_accounts: List[str] = field(default_factory=list)
    mule_accounts: List[str] = field(default_factory=list)
