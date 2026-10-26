# MCP Crawl4AI RAG Server with Knowledge Graph System

## Execution Environment: WSL ↔ Windows Bridge

Claude Code runs inside **WSL (Windows Subsystem for Linux)** while most applications, services, and tools reside on the **Windows host system**. This creates a hybrid execution environment requiring awareness of both worlds.

### Key Concepts

| Context | Path Format | Example |
|---------|-------------|---------|
| WSL filesystem | `/mnt/e/...` | `/mnt/e/ZedBang/MPC2/3rd/mcp-crawl4ai-rag` |
| Windows filesystem | `E:\...` | `E:\ZedBang\MPC2\3rd\mcp-crawl4ai-rag` |
| WSL native | `/home/...`, `/root/...` | `/root/.local/bin/uv` |

### Cross-Platform Execution Patterns

**Running Windows executables from WSL:**
```bash
# Direct .exe invocation (Windows apps accessible from WSL)
powershell.exe -Command "Get-Process"
cmd.exe /c "dir E:\\ZedBang"

# Path conversion when needed
wslpath -w /mnt/e/ZedBang  # Returns: E:\ZedBang
wslpath -u 'E:\ZedBang'    # Returns: /mnt/e/ZedBang
```

**Python and uv execution:**
```bash
# uv lives in WSL but manages Python environments
/root/.local/bin/uv run python src/crawl4ai_mcp.py

# System Python in WSL
python3 /mnt/e/ZedBang/MPC2/Cust/ScreenBang/src/mcp_server.py
```

**Capturing Windows console output:**
```bash
# PowerShell output flows back to WSL stdout
powershell.exe -Command "Get-WmiObject Win32_VideoController | Select-Object Name"

# Running Windows Python (if installed)
/mnt/c/Python312/python.exe script.py
```

### Common Bridge Scenarios

1. **File operations**: Use WSL paths (`/mnt/e/...`) for all file I/O - WSL handles translation
2. **Windows services**: Call via `powershell.exe` or direct `.exe` invocation
3. **Neo4j**: Runs as Windows service, accessible at `localhost:7687` from WSL
4. **Browser automation**: Crawl4AI uses Playwright which bridges to Windows Chrome/Chromium
5. **Network services**: `localhost` works bidirectionally between WSL and Windows

### Troubleshooting Cross-Platform Issues

```bash
# Verify WSL can see Windows drives
ls /mnt/c /mnt/d /mnt/e

# Test PowerShell bridge
powershell.exe -Command "Write-Host 'Bridge OK'"

# Check Windows service from WSL
powershell.exe -Command "Get-Service neo4j"
```

---

## Overview
This MCP server provides web crawling, RAG capabilities, and a specialized Knowledge Graph system designed for massive codebases like Unreal Engine. It enables:
- Web crawling and content extraction
- Semantic search over crawled data
- Phased knowledge graph building for large repositories
- Agent-specific tools for research vs. building tasks

## Agent Type Quick Reference

### 🔍 If You Are a RESEARCH Agent (Finding Information)
**Your job**: Find code patterns, understand implementations, answer questions

**Use these tools**:
```bash
# Query the knowledge graph
python _DevPlan/scripts/research/query_phase_graph.py --query "Your question"

# Find patterns
python _DevPlan/scripts/research/find_ue_patterns.py --pattern "ComponentSystem"

# MCP tools available:
- mcp_research_query
- mcp_find_patterns
- mcp_get_dependencies
```

**Never**: Modify the graph, run maintenance scripts, delete data

---

### 🔨 If You Are a BUILDING Agent (Creating Development Plans)
**Your job**: Review code structure, create development plans, suggest implementations

**Use these tools**:
```bash
# Review before planning
python _DevPlan/scripts/building/review_for_planning.py --feature "feature_name"

# Generate templates
python _DevPlan/scripts/building/generate_ue_boilerplate.py --class-type Actor

# MCP tools available:
- mcp_review_for_plan
- mcp_suggest_patterns
- mcp_generate_template
```

**Focus on**: Understanding patterns, identifying dependencies, following conventions

---

### 🔧 If You Are a MAINTENANCE Agent (Updating Graphs)
**Your job**: Build/update knowledge graphs, manage phases, validate data

**Use these tools**:
```bash
# Analyze UE phase
python _DevPlan/scripts/maintenance/analyze_ue_phase.py --phase core --append

# Validate graph
python _DevPlan/scripts/maintenance/validate_graph.py --phase core

# Export/Import
python _DevPlan/scripts/maintenance/export_import_phase.py --export --phase core
```

---

## Development Plan Location
**Full development plan and documentation**: `_DevPlan/DEVELOPMENT_PLAN.md`
**Agent-specific instructions**: `_DevPlan/AGENT_INSTRUCTIONS.md`

## Installation Location
- **Path**: `/mnt/e/ZedBang/MPC2/3rd/mcp-crawl4ai-rag`
- **Windows Path**: `E:\ZedBang\MPC2\3rd\mcp-crawl4ai-rag`
- **Python**: 3.12+ (managed by uv in WSL)
- **Environment**: Virtual environment at `.venv/`

## Configuration
- **Transport**: stdio (configured for Claude Code integration)
- **Environment file**: `.env` (contains API keys and feature flags)
- **Claude settings**: Configured in `/root/.config/claude/settings.json`

## Management Scripts
- **Start**: `./start_mcp.sh` - Start server in background
- **Stop**: `./stop_mcp.sh` - Stop server gracefully  
- **Logs**: `/tmp/mcp-crawl4ai-rag.log`

## Features Enabled
- ✅ Contextual Embeddings
- ✅ Hybrid Search (vector + keyword)
- ✅ Agentic RAG (code extraction)
- ❌ Reranking (disabled for performance)
- ✅ Knowledge Graph (Neo4j installed and configured)

## Knowledge Graph Status
- **Neo4j**: Installed and running on localhost:7687
- **Credentials**: neo4j / neo4j123
- **Current graphs**: 
  - mcp-crawl4ai-rag (8 files, 22 classes, 45 functions)
  - graphiti (88 files, 143 classes)

## Unreal Engine Phased Analysis

### Phase Structure
The system analyzes UE in manageable phases:
1. **Core**: Core, CoreUObject, ApplicationCore
2. **Rendering**: Renderer, RenderCore, RHI
3. **Gameplay**: Engine, GameplayAbilities, GameplayTags
4. **Editor**: UnrealEd, EditorSubsystem
5. **Plugins**: Project-specific plugins

### Graph Storage
All graphs stored in: `.crawl4ai/`
```
.crawl4ai/
├── knowledge_graphs/     # Neo4j data by phase
├── visualizations/       # HTML outputs
├── phase_data/          # Phase-specific exports
└── analysis_reports/    # Validation reports
```

## Quick Commands by Agent Type

### Research Commands
```bash
# Query knowledge
"Find all Actor-derived classes in gameplay phase"

# Find patterns
"Show similar implementations to PlayerController"

# Get dependencies
"What modules does Engine depend on?"
```

### Building Commands
```bash
# Review for planning
"Review existing inventory systems before creating new one"

# Get suggestions
"Suggest pattern for multiplayer game mode"

# Generate template
"Create template for custom Actor with replication"
```

### Maintenance Commands
```bash
# Add new phase
"Analyze core module and append to graph"

# Validate
"Check graph completeness for rendering phase"

# Export
"Export gameplay phase for backup"
```

## Performance Considerations

### For Large Codebases (Unreal Engine)
- Process in phases (max 10,000 files per phase)
- Use `--append` mode to build incrementally
- Skip generated files (`*.generated.h`)
- Run during off-hours for large analyses

### Query Optimization
- Always specify phase to limit scope
- Use LIMIT in Cypher queries
- Cache frequently used results
- Query specific modules when possible

## Troubleshooting

### Neo4j Not Connecting
```bash
# Start Neo4j
neo4j start

# Check status
neo4j status

# Test connection
cypher-shell -u neo4j -p neo4j123
```

### Out of Memory
```bash
# Limit file processing
--file-limit 5000

# Increase Neo4j memory
export NEO4J_HEAP_MEMORY="4G"
```

### MCP Tools Not Loading
- Restart Claude Code session
- Check `/tmp/mcp-crawl4ai-rag.log`
- Verify `.env` configuration

## Related Documentation
- **Development Plan**: `_DevPlan/DEVELOPMENT_PLAN.md`
- **Agent Instructions**: `_DevPlan/AGENT_INSTRUCTIONS.md`
- **Original README**: `README.md`
- **Phase Definitions**: `_DevPlan/docs/PHASE_DEFINITIONS.md`

## Important Notes
- **Research agents**: Never modify the graph
- **Building agents**: Always review before generating
- **Maintenance agents**: Use MERGE not CREATE to avoid duplicates
- **All agents**: Specify phase for better performance