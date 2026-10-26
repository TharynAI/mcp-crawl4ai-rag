#!/usr/bin/env python3
"""
Create HTML visualization of the knowledge graph and save to proper location
"""

import asyncio
import logging
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

async def main():
    """Create visualization and save to proper location"""
    load_dotenv()
    
    # Import after setting up path
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "knowledge_graphs"))
    from parse_repo_into_neo4j import DirectNeo4jExtractor
    
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'neo4j123')
    
    logger.info("Creating knowledge graph visualization")
    
    extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        await extractor.initialize()
        
        # Query all nodes and relationships for mcp-crawl4ai-rag
        query = """
        MATCH (n:Repository {name: 'mcp-crawl4ai-rag'})-[:CONTAINS]->(f:File)
        OPTIONAL MATCH (f)-[:DEFINES]->(c:Class)
        OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
        OPTIONAL MATCH (f)-[:DEFINES]->(func:Function)
        RETURN n, f, c, m, func
        """
        
        result = await extractor.driver.execute_query(query)
        nodes = []
        links = []
        node_ids = set()
        
        # Process results
        for record in result.records:
            repo = record['n']
            file = record['f']
            class_node = record['c']
            method = record['m']
            function = record['func']
            
            # Add repository node
            if repo and repo.element_id not in node_ids:
                nodes.append({
                    'id': repo.element_id,
                    'name': repo['name'],
                    'type': 'repository',
                    'group': 1
                })
                node_ids.add(repo.element_id)
            
            # Add file node
            if file and file.element_id not in node_ids:
                nodes.append({
                    'id': file.element_id,
                    'name': file['name'],
                    'path': file['path'],
                    'type': 'file',
                    'group': 2
                })
                node_ids.add(file.element_id)
                
                # Link repo -> file
                if repo:
                    links.append({
                        'source': repo.element_id,
                        'target': file.element_id,
                        'type': 'contains'
                    })
            
            # Add class node
            if class_node and class_node.element_id not in node_ids:
                nodes.append({
                    'id': class_node.element_id,
                    'name': class_node['name'],
                    'type': 'class',
                    'group': 3
                })
                node_ids.add(class_node.element_id)
                
                # Link file -> class
                if file:
                    links.append({
                        'source': file.element_id,
                        'target': class_node.element_id,
                        'type': 'defines'
                    })
            
            # Add method node
            if method and method.element_id not in node_ids:
                nodes.append({
                    'id': method.element_id,
                    'name': method['name'],
                    'type': 'method',
                    'group': 4
                })
                node_ids.add(method.element_id)
                
                # Link class -> method
                if class_node:
                    links.append({
                        'source': class_node.element_id,
                        'target': method.element_id,
                        'type': 'has_method'
                    })
            
            # Add function node
            if function and function.element_id not in node_ids:
                nodes.append({
                    'id': function.element_id,
                    'name': function['name'],
                    'type': 'function',
                    'group': 5
                })
                node_ids.add(function.element_id)
                
                # Link file -> function
                if file:
                    links.append({
                        'source': file.element_id,
                        'target': function.element_id,
                        'type': 'defines'
                    })
        
        # Create the visualization HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MCP Crawl4AI RAG - Knowledge Graph Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #333;
            text-align: center;
            margin-bottom: 10px;
        }}
        
        .info {{
            text-align: center;
            color: #666;
            margin-bottom: 20px;
        }}
        
        .legend {{
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .legend-color {{
            width: 15px;
            height: 15px;
            border-radius: 50%;
        }}
        
        #graph {{
            width: 100%;
            height: 600px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 10px;
            background: rgba(0, 0, 0, 0.8);
            color: white;
            border-radius: 4px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>MCP Crawl4AI RAG Knowledge Graph</h1>
        <div class="info">
            Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
            {len(nodes)} nodes, {len(links)} relationships
        </div>
        
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background-color: #ff7f0e;"></div>
                <span>Repository</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #1f77b4;"></div>
                <span>File</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #2ca02c;"></div>
                <span>Class</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #d62728;"></div>
                <span>Method</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #9467bd;"></div>
                <span>Function</span>
            </div>
        </div>
        
        <div id="graph"></div>
        <div class="tooltip"></div>
    </div>

    <script>
        const data = {{
            nodes: {json.dumps(nodes)},
            links: {json.dumps(links)}
        }};
        
        const width = 1160;
        const height = 600;
        
        const color = d3.scaleOrdinal(d3.schemeCategory10);
        
        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);
        
        const tooltip = d3.select(".tooltip");
        
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collision", d3.forceCollide().radius(30));
        
        const link = svg.append("g")
            .selectAll("line")
            .data(data.links)
            .join("line")
            .attr("stroke", "#999")
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2);
        
        const node = svg.append("g")
            .selectAll("circle")
            .data(data.nodes)
            .join("circle")
            .attr("r", d => d.type === 'repository' ? 12 : d.type === 'file' ? 8 : 6)
            .attr("fill", d => color(d.group))
            .attr("stroke", "#fff")
            .attr("stroke-width", 2);
        
        const label = svg.append("g")
            .selectAll("text")
            .data(data.nodes)
            .join("text")
            .text(d => d.name)
            .attr("font-size", "10px")
            .attr("dx", 15)
            .attr("dy", 4);
        
        node.on("mouseover", function(event, d) {{
            tooltip.transition().duration(200).style("opacity", .9);
            tooltip.html(`
                <strong>${{d.type.toUpperCase()}}</strong><br/>
                Name: ${{d.name}}<br/>
                ${{d.path ? `Path: ${{d.path}}<br/>` : ''}}
                ID: ${{d.id}}
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", function(d) {{
            tooltip.transition().duration(500).style("opacity", 0);
        }});
        
        node.call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
        
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
                
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
                
            label
                .attr("x", d => d.x)
                .attr("y", d => d.y);
        }});
        
        function dragstarted(event, d) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }}
        
        function dragged(event, d) {{
            d.fx = event.x;
            d.fy = event.y;
        }}
        
        function dragended(event, d) {{
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }}
    </script>
</body>
</html>
"""
        
        # Save to .crawl4ai/visualizations directory
        vis_dir = Path(".crawl4ai/visualizations")
        vis_dir.mkdir(parents=True, exist_ok=True)
        
        html_file = vis_dir / "mcp-crawl4ai-rag_knowledge_graph.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Also save the raw data as JSON
        json_file = vis_dir / "mcp-crawl4ai-rag_graph_data.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump({
                'nodes': nodes,
                'links': links,
                'metadata': {
                    'repository': 'mcp-crawl4ai-rag',
                    'generated_at': datetime.now().isoformat(),
                    'node_count': len(nodes),
                    'link_count': len(links)
                }
            }, f, indent=2)
        
        print(f"\\n=== Visualization Created Successfully ===")
        print(f"HTML file: {html_file.absolute()}")
        print(f"JSON data: {json_file.absolute()}")
        print(f"Nodes: {len(nodes)}")
        print(f"Links: {len(links)}")
        print(f"\\nTo view:")
        print(f"1. Open: file://{html_file.absolute()}")
        print(f"2. Or Neo4j Browser: http://localhost:7474")
        
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")
        raise
    finally:
        await extractor.close()

if __name__ == "__main__":
    asyncio.run(main())