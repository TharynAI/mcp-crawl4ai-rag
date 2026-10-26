# Unreal Engine Knowledge Graph Development Plan

## Overview
This development plan organizes the knowledge graph system for Unreal Engine's massive codebase, with clear separation between research agents (finding information) and building agents (creating code).

## Project Structure

```
_DevPlan/
├── DEVELOPMENT_PLAN.md (this file)
├── AGENT_INSTRUCTIONS.md (what each agent type should use)
├── docs/
│   ├── RESEARCH_AGENT_GUIDE.md
│   ├── BUILDING_AGENT_GUIDE.md
│   └── PHASE_DEFINITIONS.md
├── scripts/
│   ├── research/          # Scripts for agents finding information
│   ├── building/          # Scripts for agents creating development plans
│   ├── maintenance/       # Scripts for graph updates and management
│   └── visualization/     # Scripts for generating visual outputs
└── configs/
    ├── ue_modules.json    # UE module definitions by phase
    └── agent_permissions.json

.crawl4ai/                  # Data storage (outside _DevPlan)
├── knowledge_graphs/       # Neo4j data by phase
├── visualizations/         # HTML outputs
└── phase_data/            # Phase-specific exports
```

## Development Phases

### Phase 1: Core Scripts Foundation (Week 1)
**Goal**: Create base infrastructure for phased graph building

#### Scripts to Develop:

1. **`scripts/maintenance/analyze_ue_phase.py`**
   - Purpose: Analyze specific UE modules/subsystems
   - Features:
     - `--phase` parameter (core, rendering, gameplay, editor, plugins)
     - `--append` mode to add without clearing
     - `--file-limit` for chunked processing
     - `--skip-generated` to ignore .generated.h files
     - Progress tracking with resume capability

2. **`scripts/research/query_phase_graph.py`**
   - Purpose: Research agents query existing knowledge
   - Features:
     - Natural language to Cypher query conversion
     - Phase-aware queries (only search relevant phases)
     - Return formatted results for agent consumption
     - Cross-reference detection

3. **`scripts/building/review_for_planning.py`**
   - Purpose: Building agents review graph before creating plans
   - Features:
     - Analyze existing implementations
     - Identify patterns and dependencies
     - Generate development context report
     - Suggest implementation approaches based on codebase

### Phase 2: UE-Specific Enhancements (Week 2)
**Goal**: Handle Unreal Engine's unique patterns

#### Scripts to Develop:

4. **`scripts/maintenance/parse_ue_macros.py`**
   - Handle UCLASS, USTRUCT, UENUM, UPROPERTY, UFUNCTION
   - Extract reflection metadata
   - Link Blueprint relationships

5. **`scripts/research/find_ue_patterns.py`**
   - Search for UE design patterns (Actor, Component, Subsystem)
   - Find similar implementations
   - Identify module dependencies from .Build.cs files

6. **`scripts/building/generate_ue_boilerplate.py`**
   - Generate UE-compliant class templates
   - Create proper header/cpp pairs
   - Include necessary macros based on graph knowledge

### Phase 3: Agent Integration (Week 3)
**Goal**: Seamless MCP integration for different agent types

#### Scripts to Develop:

7. **`scripts/research/mcp_research_endpoint.py`**
   - MCP tool wrapper for research operations
   - Rate limiting and caching
   - Returns concise, relevant results

8. **`scripts/building/mcp_planning_endpoint.py`**
   - MCP tool for development planning
   - Analyzes graph for best practices
   - Generates structured development plans

9. **`scripts/visualization/generate_context_view.py`**
   - Creates focused visualizations for specific queries
   - Exports as HTML or image for agent review

### Phase 4: Performance & Scale (Week 4)
**Goal**: Handle UE's massive size efficiently

#### Scripts to Develop:

10. **`scripts/maintenance/parallel_analyzer.py`**
    - Multi-threaded file parsing
    - Batch Neo4j commits
    - Memory-efficient processing

11. **`scripts/maintenance/export_import_phase.py`**
    - Export phases for backup
    - Import to new engine versions
    - Merge multiple phases

12. **`scripts/maintenance/validate_graph.py`**
    - Check graph completeness
    - Identify missing relationships
    - Report analysis coverage

## Agent Type Definitions

### Research Agents
**Purpose**: Find information, understand existing code, answer questions
**Primary Scripts**:
- `query_phase_graph.py`
- `find_ue_patterns.py`
- `mcp_research_endpoint.py`

### Building Agents
**Purpose**: Create development plans, generate code, implement features
**Primary Scripts**:
- `review_for_planning.py`
- `generate_ue_boilerplate.py`
- `mcp_planning_endpoint.py`

### Maintenance Agents
**Purpose**: Update graphs, manage phases, validate data
**Primary Scripts**:
- `analyze_ue_phase.py`
- `export_import_phase.py`
- `validate_graph.py`

## Implementation Priority

### Immediate (Must Have)
1. `analyze_ue_phase.py` - Core functionality
2. `query_phase_graph.py` - Basic research capability
3. `review_for_planning.py` - Planning support

### High Priority (Week 1-2)
4. `parse_ue_macros.py` - UE-specific support
5. `find_ue_patterns.py` - Pattern recognition
6. MCP endpoints for integration

### Medium Priority (Week 3-4)
7. Visualization scripts
8. Performance optimizations
9. Validation and export tools

## Success Metrics

1. **Coverage**: Ability to analyze 10,000+ files per phase
2. **Query Speed**: Research queries return in <2 seconds
3. **Accuracy**: 95% accurate UE pattern recognition
4. **Memory**: Stay under 8GB RAM during analysis
5. **Integration**: Seamless MCP tool usage by agents

## Configuration Examples

### `configs/ue_modules.json`
```json
{
  "phases": {
    "core": {
      "modules": ["Core", "CoreUObject", "ApplicationCore"],
      "priority": 1,
      "dependencies": []
    },
    "rendering": {
      "modules": ["Renderer", "RenderCore", "RHI", "MaterialShaderQualitySettings"],
      "priority": 2,
      "dependencies": ["core"]
    },
    "gameplay": {
      "modules": ["Engine", "GameplayAbilities", "GameplayTags", "GameplayTasks"],
      "priority": 3,
      "dependencies": ["core"]
    }
  }
}
```

### `configs/agent_permissions.json`
```json
{
  "research": {
    "allowed_operations": ["query", "read", "search", "visualize"],
    "denied_operations": ["modify", "delete", "create"],
    "rate_limit": 100
  },
  "building": {
    "allowed_operations": ["query", "read", "analyze", "generate", "suggest"],
    "denied_operations": ["modify_graph", "delete"],
    "rate_limit": 50
  }
}
```

## Next Steps

1. Review and approve this plan
2. Begin with Phase 1 core scripts
3. Test with small UE module (e.g., ApplicationCore)
4. Iterate based on agent feedback
5. Scale to full engine analysis

## Notes for Agents

- **Research agents**: Focus on `scripts/research/` folder
- **Building agents**: Use `scripts/building/` for planning
- **Never modify the graph** during research/building operations
- **Always specify phase** when querying to improve performance
- **Check AGENT_INSTRUCTIONS.md** for your specific role