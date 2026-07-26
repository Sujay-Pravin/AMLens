import networkx as nx
import numpy as np
import pandas as pd

from .schemas import GraphMetrics

CYCLE_LENGTH_BOUND = 4
MAX_CYCLES_REPORTED = 50

HUB_MIN_DEGREE = 3
HUB_STD_MULTIPLIER = 2.0

MULE_MIN_DEGREE = 2
MULE_AMOUNT_TOLERANCE = 0.15


class GraphAnalyzer:
    """
    Builds a transaction graph and computes structural risk metrics.
    """

    @staticmethod
    def build_graph(df: pd.DataFrame) -> nx.DiGraph:

        graph = nx.DiGraph()

        for row in df.itertuples(index=False):
            sender = getattr(row, "sender_entity_id")
            receiver = getattr(row, "receiver_entity_id")
            amount = float(getattr(row, "amount_paid", 0.0) or 0.0)

            if graph.has_edge(sender, receiver):
                edge = graph[sender][receiver]
                edge["count"] += 1
                edge["amount"] += amount
            else:
                graph.add_edge(sender, receiver, count=1, amount=amount)

        return graph

    @staticmethod
    def analyze(df: pd.DataFrame) -> GraphMetrics:

        graph = GraphAnalyzer.build_graph(df)

        in_degree = dict(graph.in_degree())
        out_degree = dict(graph.out_degree())

        pagerank = (
            nx.pagerank(graph, weight="amount")
            if graph.number_of_edges() > 0
            else {}
        )

        num_components = nx.number_weakly_connected_components(graph)

        cycles = []
        for cycle in nx.simple_cycles(graph, length_bound=CYCLE_LENGTH_BOUND):
            cycles.append(list(cycle))
            if len(cycles) >= MAX_CYCLES_REPORTED:
                break

        total_degrees = np.array(
            [in_degree[n] + out_degree[n] for n in graph.nodes()],
            dtype=np.float64,
        )
        hub_threshold = HUB_MIN_DEGREE
        if total_degrees.size > 0:
            hub_threshold = max(
                HUB_MIN_DEGREE,
                total_degrees.mean() + HUB_STD_MULTIPLIER * total_degrees.std(),
            )

        hub_accounts = sorted(
            [
                node for node in graph.nodes()
                if (in_degree[node] + out_degree[node]) >= hub_threshold
            ],
            key=lambda n: in_degree[n] + out_degree[n],
            reverse=True,
        )

        mule_accounts = []
        for node in graph.nodes():
            if in_degree[node] < MULE_MIN_DEGREE or out_degree[node] < MULE_MIN_DEGREE:
                continue

            total_in = sum(
                data["amount"] for _, _, data in graph.in_edges(node, data=True)
            )
            total_out = sum(
                data["amount"] for _, _, data in graph.out_edges(node, data=True)
            )

            largest = max(total_in, total_out, 1e-9)
            if abs(total_in - total_out) / largest <= MULE_AMOUNT_TOLERANCE:
                mule_accounts.append(node)

        return GraphMetrics(
            node_count=graph.number_of_nodes(),
            edge_count=graph.number_of_edges(),
            num_components=num_components,
            in_degree=in_degree,
            out_degree=out_degree,
            pagerank=pagerank,
            cycles=cycles,
            hub_accounts=hub_accounts,
            mule_accounts=mule_accounts,
        )
