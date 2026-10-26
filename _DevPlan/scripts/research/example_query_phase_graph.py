#!/usr/bin/env python3
"""
Example implementation of query_phase_graph.py for research agents.
This script shows how research agents should query the knowledge graph.

Usage:
    python query_phase_graph.py --query "Find all Actor classes" --phase gameplay
    python query_phase_graph.py --natural "How does spawning work?"
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add knowledge_graphs to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "knowledge_graphs"))

async def natural_to_cypher(query: str, phase: str = None) -> str:
    """
    Convert natural language query to Cypher.
    In production, this could use an LLM for better conversion.
    """
    query_lower = query.lower()
    
    # Build phase filter if specified
    phase_filter = f" {{phase: '{phase}'}}" if phase else ""
    
    # Common query patterns
    if "all" in query_lower and "class" in query_lower:
        if "actor" in query_lower:
            return f"MATCH (c:Class{phase_filter}) WHERE c.name CONTAINS 'Actor' RETURN c.name, c.file_path LIMIT 50"
        else:
            return f"MATCH (c:Class{phase_filter}) RETURN c.name, c.file_path LIMIT 100"
    
    elif "methods" in query_lower or "functions" in query_lower:
        # Extract class name if mentioned
        if "aactor" in query_lower or "actor" in query_lower:
            return f"MATCH (c:Class {{name: 'AActor'}}{phase_filter})-[:HAS_METHOD]->(m:Method) RETURN c.name, collect(m.name) as methods"
        else:
            return f"MATCH (c:Class{phase_filter})-[:HAS_METHOD]->(m:Method) RETURN c.name, collect(m.name) as methods LIMIT 20"
    
    elif "inherit" in query_lower or "derive" in query_lower:
        if "from" in query_lower:
            # Extract parent class name
            words = query.split()
            if "from" in words:
                parent_idx = words.index("from") + 1
                if parent_idx < len(words):
                    parent = words[parent_idx]
                    return f"MATCH (child:Class{phase_filter})-[:INHERITS]->(parent:Class {{name: '{parent}'}}) RETURN child.name, parent.name"
        return f"MATCH (child:Class{phase_filter})-[:INHERITS]->(parent:Class) RETURN child.name, parent.name LIMIT 50"
    
    elif "spawn" in query_lower:
        return f"""
        MATCH (c:Class{phase_filter})-[:HAS_METHOD]->(m:Method)
        WHERE m.name CONTAINS 'Spawn' OR m.name CONTAINS 'spawn'
        RETURN c.name, m.name, m.parameters
        LIMIT 30
        """
    
    elif "component" in query_lower:
        return f"""
        MATCH (c:Class{phase_filter})
        WHERE c.name CONTAINS 'Component' OR c.parent_class CONTAINS 'Component'
        RETURN c.name, c.parent_class
        LIMIT 50
        """
    
    elif "depend" in query_lower:
        return f"""
        MATCH (f1:File{phase_filter})-[:IMPORTS]->(f2:File)
        RETURN f1.name, collect(f2.name) as dependencies
        LIMIT 30
        """
    
    else:
        # Generic search
        return f"""
        MATCH (n{phase_filter})
        WHERE n.name CONTAINS '{query.replace("'", "")}'
        RETURN labels(n)[0] as Type, n.name, n.file_path
        LIMIT 50
        """

async def execute_query(cypher: str) -> List[Dict[str, Any]]:
    """Execute Cypher query against Neo4j."""
    from parse_repo_into_neo4j import DirectNeo4jExtractor
    
    # Get Neo4j credentials from environment
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'neo4j123')
    
    extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        await extractor.initialize()
        result = await extractor.driver.execute_query(cypher)
        
        # Format results
        formatted_results = []
        for record in result.records:
            formatted_results.append(dict(record))
        
        return formatted_results
        
    finally:
        await extractor.close()

def format_results(results: List[Dict[str, Any]], query: str) -> str:
    """Format results for display to research agent."""
    if not results:
        return f"No results found for query: {query}"
    
    output = [f"Found {len(results)} results for: {query}\n"]
    
    for i, result in enumerate(results[:20], 1):  # Limit display to 20
        output.append(f"{i}. ", )
        for key, value in result.items():
            if isinstance(value, list):
                output.append(f"{key}: {', '.join(str(v) for v in value[:10])}")
                if len(value) > 10:
                    output.append(f"... and {len(value) - 10} more")
            else:
                output.append(f"{key}: {value}")
        output.append("")
    
    if len(results) > 20:
        output.append(f"\n... and {len(results) - 20} more results")
    
    return "\n".join(output)

async def main():
    parser = argparse.ArgumentParser(description="Query UE knowledge graph for research")
    parser.add_argument("--query", type=str, help="Natural language query")
    parser.add_argument("--cypher", type=str, help="Direct Cypher query")
    parser.add_argument("--phase", type=str, choices=["core", "rendering", "gameplay", "editor", "plugins"],
                       help="Limit search to specific phase")
    parser.add_argument("--format", choices=["text", "json"], default="text",
                       help="Output format")
    
    args = parser.parse_args()
    
    if not args.query and not args.cypher:
        print("Error: Provide either --query or --cypher")
        sys.exit(1)
    
    # Convert natural language to Cypher if needed
    if args.query:
        cypher = await natural_to_cypher(args.query, args.phase)
        print(f"Generated Cypher: {cypher}\n")
    else:
        cypher = args.cypher
    
    # Execute query
    try:
        results = await execute_query(cypher)
        
        # Format output
        if args.format == "json":
            import json
            print(json.dumps(results, indent=2))
        else:
            print(format_results(results, args.query or args.cypher))
            
    except Exception as e:
        print(f"Error executing query: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())