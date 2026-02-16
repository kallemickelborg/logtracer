"""Core graph models for trace capture."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, computed_field, model_validator


class NodeStatus(StrEnum):
    """Lifecycle state for a node."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class EdgeType(StrEnum):
    """Relationship semantics between nodes."""

    CAUSED_BY = "caused_by"
    DATA_FLOW = "data_flow"
    BRANCHED_FROM = "branched_from"
    RETRY_OF = "retry_of"
    FALLBACK_OF = "fallback_of"


class NodeType(StrEnum):
    """Recommended node type vocabulary."""

    LLM_CALL = "llm_call"
    TOOL_CALL = "tool_call"
    DECISION = "decision"
    RETRIEVAL = "retrieval"
    TRANSFORMATION = "transformation"
    VALIDATION = "validation"
    HUMAN_INPUT = "human_input"
    SUB_AGENT = "sub_agent"
    CUSTOM = "custom"


class Node(BaseModel):
    """Single unit of execution in a trace."""

    model_config = ConfigDict(strict=True)

    id: str = Field(default_factory=lambda: uuid4().hex)
    sequence_number: int
    name: str
    node_type: str
    status: NodeStatus = NodeStatus.PENDING
    parent_id: str | None = None
    depth: int = 0
    start_time: datetime | None = None
    end_time: datetime | None = None
    input_data: dict[str, object] = Field(default_factory=dict)
    output_data: dict[str, object] = Field(default_factory=dict)
    annotations: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    error: str | None = None
    error_type: str | None = None
    error_traceback: str | None = None

    @computed_field(return_type=float | None)
    @property
    def duration_ms(self) -> float | None:
        """Duration in milliseconds when both timestamps are available."""
        if self.start_time is None or self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000.0


class Edge(BaseModel):
    """Directional relationship between two nodes."""

    model_config = ConfigDict(strict=True)

    source_id: str
    target_id: str
    edge_type: EdgeType = EdgeType.CAUSED_BY
    label: str = ""
    metadata: dict[str, object] = Field(default_factory=dict)


class TraceGraph(BaseModel):
    """Root trace structure containing nodes and edges."""

    model_config = ConfigDict(strict=True)

    schema_version: str = "0.1.0"
    trace_id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = ""
    nodes: dict[str, Node] = Field(default_factory=dict)
    edges: list[Edge] = Field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    _sequence_counter: int = PrivateAttr(default=0)

    @computed_field(return_type=float | None)
    @property
    def duration_ms(self) -> float | None:
        """Trace duration in milliseconds."""
        if self.start_time is None or self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds() * 1000.0

    @property
    def root_nodes(self) -> list[Node]:
        """Nodes that do not have a parent."""
        return [node for node in self.nodes.values() if node.parent_id is None]

    @property
    def failed_nodes(self) -> list[Node]:
        """Nodes that ended in failed status."""
        return [node for node in self.nodes.values() if node.status == NodeStatus.FAILED]

    def next_sequence_number(self) -> int:
        """Allocate the next deterministic sequence number for this trace."""
        value = self._sequence_counter
        self._sequence_counter += 1
        return value

    def add_node(self, node: Node) -> None:
        """Insert a node by id."""
        self.nodes[node.id] = node

    def add_edge(self, edge: Edge) -> None:
        """Insert an edge after validating node references exist."""
        if edge.source_id not in self.nodes:
            raise ValueError(f"Unknown edge source node id: {edge.source_id}")
        if edge.target_id not in self.nodes:
            raise ValueError(f"Unknown edge target node id: {edge.target_id}")
        self.edges.append(edge)

    @model_validator(mode="after")
    def validate_edge_references(self) -> TraceGraph:
        """Validate all edge references point to existing nodes."""
        for edge in self.edges:
            if edge.source_id not in self.nodes:
                raise ValueError(f"Edge source_id not found in nodes: {edge.source_id}")
            if edge.target_id not in self.nodes:
                raise ValueError(f"Edge target_id not found in nodes: {edge.target_id}")
        return self
