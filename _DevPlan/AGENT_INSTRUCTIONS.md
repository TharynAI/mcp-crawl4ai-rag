# Agent Instructions for Knowledge Graph System

## Quick Start by Agent Type

### 🔍 Research Agent (Finding Information)

**Your Purpose**: Find existing code patterns, understand implementations, answer questions about the codebase.

**Scripts You Should Use**:
```bash
# Primary research tool - Query the knowledge graph
python scripts/research/query_phase_graph.py --query "How does Actor spawning work?" --phase gameplay

# Find similar patterns in codebase
python scripts/research/find_ue_patterns.py --pattern "ComponentSystem" --limit 10

# Get visual context for complex relationships
python scripts/visualization/generate_context_view.py --class "AActor" --depth 2
```

**MCP Tools Available**:
- `mcp_research_query` - Natural language queries against graph
- `mcp_find_patterns` - Pattern matching in codebase
- `mcp_get_dependencies` - Find module/class dependencies

**What You Should NOT Do**:
- ❌ Modify the graph
- ❌ Run maintenance scripts
- ❌ Delete or alter any data

**Example Workflow**:
```python
# 1. Check what phases are available
result = mcp_research_query("list available phases")

# 2. Query specific information
actor_info = mcp_research_query("Show AActor class methods in gameplay phase")

# 3. Find similar implementations
patterns = mcp_find_patterns("classes inheriting from UObject with Tick functions")
```

---

### 🔨 Building Agent (Creating Development Plans)

**Your Purpose**: Review existing code structure before creating new features, generate development plans, suggest implementation approaches.

**Scripts You Should Use**:
```bash
# Review graph before planning
python scripts/building/review_for_planning.py --feature "multiplayer_system" --phase gameplay,networking

# Generate UE-compliant boilerplate
python scripts/building/generate_ue_boilerplate.py --class-type Actor --name "MyCustomActor"

# Analyze patterns for best practices
python scripts/building/analyze_best_practices.py --subsystem "Animation"
```

**MCP Tools Available**:
- `mcp_review_for_plan` - Analyze graph for development planning
- `mcp_suggest_patterns` - Get implementation suggestions
- `mcp_generate_template` - Create UE-compliant templates

**What You Should Focus On**:
- ✅ Understanding existing patterns before building
- ✅ Identifying dependencies and interfaces
- ✅ Following established conventions in the codebase
- ✅ Generating compliant code structure

**Example Workflow**:
```python
# 1. Review existing implementations
review = mcp_review_for_plan("Creating new GameMode", phases=["gameplay"])

# 2. Get pattern suggestions
patterns = mcp_suggest_patterns("GameMode with custom player spawning")

# 3. Generate template
template = mcp_generate_template(
    class_type="GameMode",
    name="MyCustomGameMode",
    includes_suggested=True
)
```

---

### 🔧 Maintenance Agent (Updating Graphs)

**Your Purpose**: Build and update knowledge graphs, manage phases, validate data integrity.

**Scripts You Should Use**:
```bash
# Analyze new phase of UE
python scripts/maintenance/analyze_ue_phase.py --phase rendering --append

# Validate graph completeness
python scripts/maintenance/validate_graph.py --phase core --check-relationships

# Export phase for backup
python scripts/maintenance/export_import_phase.py --export --phase core --output backups/
```

**What You Should Monitor**:
- ⚠️ Memory usage during large analyses
- ⚠️ Duplicate nodes (use MERGE instead of CREATE)
- ⚠️ Incomplete relationships
- ⚠️ Generated files that should be skipped

---

## Script Directory Guide

### `/scripts/research/` - Information Discovery
```
query_phase_graph.py       # Natural language to Cypher queries
find_ue_patterns.py        # Pattern matching across codebase
search_dependencies.py     # Module and class dependency search
mcp_research_endpoint.py   # MCP integration for research
```

### `/scripts/building/` - Development Planning
```
review_for_planning.py     # Analyze graph before development
generate_ue_boilerplate.py # Create UE-compliant templates
analyze_best_practices.py  # Extract patterns and conventions
suggest_implementation.py  # AI-assisted implementation suggestions
mcp_planning_endpoint.py   # MCP integration for planning
```

### `/scripts/maintenance/` - Graph Management
```
analyze_ue_phase.py        # Build graph for UE modules
parse_ue_macros.py        # Handle UCLASS, UPROPERTY, etc.
validate_graph.py         # Check graph integrity
export_import_phase.py    # Backup and migration
parallel_analyzer.py      # High-performance analysis
```

### `/scripts/visualization/` - Visual Outputs
```
generate_context_view.py   # Focused visualizations
create_flow_diagram.py    # Data flow visualizations
export_for_docs.py        # Documentation graphics
```

---

## Common Queries by Use Case

### For Research Agents

**Understanding a Class**:
```cypher
MATCH (c:Class {name: 'AActor'})-[:HAS_METHOD]->(m:Method)
RETURN c.name, collect(m.name) as methods
```

**Finding Similar Implementations**:
```cypher
MATCH (c:Class)-[:HAS_METHOD]->(m:Method {name: 'BeginPlay'})
RETURN c.name, c.file_path
LIMIT 10
```

**Checking Dependencies**:
```cypher
MATCH (f1:File)-[:IMPORTS]->(f2:File)
WHERE f1.module = 'Engine'
RETURN f1.name, collect(f2.name) as imports
```

### For Building Agents

**Review Existing Patterns**:
```cypher
MATCH (c:Class)-[:INHERITS]->(parent:Class {name: 'AActor'})
MATCH (c)-[:HAS_METHOD]->(m:Method)
RETURN c.name, parent.name, collect(m.name) as methods
```

**Find Interface Implementations**:
```cypher
MATCH (c:Class)-[:IMPLEMENTS]->(i:Interface)
WHERE i.name CONTAINS 'Tickable'
RETURN c.name, c.file_path, i.name
```

**Analyze Module Structure**:
```cypher
MATCH (m:Module {name: 'Engine'})-[:CONTAINS]->(f:File)
OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)
RETURN m.name, count(f) as files, count(c) as classes
```

---

## Performance Tips

### For Large Queries
- Always specify `--phase` to limit scope
- Use `LIMIT` in Cypher queries
- Query specific modules when possible
- Cache frequently used results

### For Graph Building
- Process in batches of 1000 files
- Use `--append` mode for incremental builds
- Skip generated files with `--skip-generated`
- Run during off-hours for large analyses

---

## Error Handling

### Common Issues and Solutions

**"Neo4j connection refused"**:
```bash
# Start Neo4j first
neo4j start
# Wait for startup
sleep 5
# Retry operation
```

**"Out of memory during analysis"**:
```bash
# Use file limit
python analyze_ue_phase.py --file-limit 5000 --phase core

# Or increase memory
export NEO4J_HEAP_MEMORY="4G"
```

**"Duplicate node error"**:
```cypher
# Use MERGE instead of CREATE
MERGE (c:Class {full_name: 'Module.ClassName'})
ON CREATE SET c.created = datetime()
ON MATCH SET c.updated = datetime()
```

---

## Quick Reference

### Environment Variables
```bash
export NEO4J_URI="bolt://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="neo4j123"
export KNOWLEDGE_GRAPH_PHASE="core"  # Current working phase
```

### Most Used Commands
```bash
# Research: Quick query
python -c "from scripts.research import query; query('Find AActor methods')"

# Building: Review before planning
python review_for_planning.py --quick --feature "inventory_system"

# Maintenance: Update single file
python analyze_ue_phase.py --single-file "Engine/Source/Runtime/Core/Public/HAL/Platform.h"
```

---

## Agent Coordination

When multiple agents work together:

1. **Research Agent** finds existing patterns
2. **Building Agent** creates plan based on findings
3. **Maintenance Agent** updates graph after implementation

Never have multiple maintenance agents running simultaneously to avoid conflicts.