# logtracer

Framework-agnostic AI agent tracing library. Records agent execution as a directed graph of nodes and edges, making invisible behavior visible and navigable.

## Install

```bash
uv venv && source .venv/bin/activate
uv sync --group dev
```

## Usage

### DI API (recommended for production / framework integration)

```python
from logtracer.core import Tracer, TracerConfig
from logtracer.storage import MemoryStore

tracer = Tracer(config=TracerConfig(), storage=MemoryStore())

with tracer.trace("agent_run") as root:
    with root.node("classify", node_type="llm_call") as step:
        step.input(query="What's the weather?")
        step.output(intent="weather")
        step.annotate("Routed to weather tool")
```

### Convenience API (quick scripts)

```python
import logtracer

logtracer.configure(storage="file://./traces")

with logtracer.trace("agent_run") as root:
    with root.node("step", node_type="tool_call") as step:
        step.input(location="Paris")
        step.output(temp=18)
```

### Decorator

```python
from logtracer import trace
from logtracer.core import trace_node

@trace_node(node_type="tool_call")
def fetch_weather(location: str) -> dict:
    return {"temp": 18}

with trace("run") as root:
    fetch_weather("Paris")
```

## CLI

```bash
logtracer inspect path/to/trace.json
logtracer inspect path/to/trace.json --json
logtracer inspect path/to/trace.json --json --output summary.json
```

## Examples

```bash
python examples/01_sequential_tool_calling.py
python examples/02_parallel_execution.py
python examples/03_retry_and_fallback.py
python examples/04_multi_agent_handoff.py
```

## Package Structure

```
src/logtracer/
  models/       # Node, Edge, TraceGraph (Pydantic v2)
  core/         # Tracer, Span, TracerConfig, context propagation, decorators
  storage/      # StorageBackend protocol, MemoryStore, FileStore
  serializers/  # JSON import/export
  renderers/    # Rich console tree renderer
  cli/          # CLI entry points (inspect)
```
