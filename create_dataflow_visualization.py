#!/usr/bin/env python3
"""
Create a data flow visualization with dark theme and directional arrows
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
    """Create data flow visualization with dark theme"""
    load_dotenv()
    
    # Import after setting up path
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "knowledge_graphs"))
    from parse_repo_into_neo4j import DirectNeo4jExtractor
    
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'neo4j123')
    
    logger.info("Creating data flow visualization")
    
    extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        await extractor.initialize()
        
        # Query for data flow relationships
        query = """
        MATCH (f:File)-[:DEFINES]->(c:Class)-[:HAS_METHOD]->(m:Method)
        OPTIONAL MATCH (f)-[:IMPORTS]->(imported:File)
        OPTIONAL MATCH (c)-[:INHERITS]->(parent:Class)
        OPTIONAL MATCH (m)-[:CALLS]->(called:Method)
        RETURN f, c, m, imported, parent, called
        LIMIT 200
        """
        
        result = await extractor.driver.execute_query(query)
        nodes = {}
        links = []
        
        # Process results with focus on flow
        for record in result.records:
            file = record['f']
            class_node = record['c']
            method = record['m']
            imported = record['imported']
            parent = record['parent']
            called = record['called']
            
            # Add nodes with hierarchical levels for better flow visualization
            if file and file.element_id not in nodes:
                nodes[file.element_id] = {
                    'id': file.element_id,
                    'label': file['name'],
                    'type': 'file',
                    'level': 0
                }
            
            if class_node and class_node.element_id not in nodes:
                nodes[class_node.element_id] = {
                    'id': class_node.element_id,
                    'label': class_node['name'],
                    'type': 'class',
                    'level': 1
                }
                # File -> Class flow
                links.append({
                    'source': file.element_id,
                    'target': class_node.element_id,
                    'type': 'defines',
                    'arrow': True
                })
            
            if method and method.element_id not in nodes:
                nodes[method.element_id] = {
                    'id': method.element_id,
                    'label': method['name'] + '()',
                    'type': 'method',
                    'level': 2
                }
                # Class -> Method flow
                links.append({
                    'source': class_node.element_id if class_node else file.element_id,
                    'target': method.element_id,
                    'type': 'contains',
                    'arrow': True
                })
            
            # Import flows
            if imported and imported.element_id not in nodes:
                nodes[imported.element_id] = {
                    'id': imported.element_id,
                    'label': imported['name'],
                    'type': 'import',
                    'level': 0
                }
                links.append({
                    'source': file.element_id,
                    'target': imported.element_id,
                    'type': 'imports',
                    'arrow': True,
                    'dashed': True
                })
        
        # Convert nodes dict to list
        nodes_list = list(nodes.values())
        
        # Create the dark theme data flow visualization HTML
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>MCP Crawl4AI RAG - Data Flow Visualization</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            font-family: 'Consolas', 'Monaco', monospace;
            margin: 0;
            padding: 0;
            background-color: #0d1117;
            color: #c9d1d9;
        }}
        
        .container {{
            width: 100%;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }}
        
        .header {{
            background: #161b22;
            padding: 15px;
            border-bottom: 1px solid #30363d;
        }}
        
        h1 {{
            margin: 0;
            font-size: 20px;
            color: #58a6ff;
        }}
        
        .info {{
            color: #8b949e;
            font-size: 12px;
            margin-top: 5px;
        }}
        
        .legend {{
            display: flex;
            gap: 20px;
            margin-top: 10px;
            font-size: 11px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 5px;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 2px;
        }}
        
        #graph {{
            flex: 1;
            background: #0d1117;
        }}
        
        .tooltip {{
            position: absolute;
            padding: 8px;
            background: #1c2128;
            color: #c9d1d9;
            border: 1px solid #30363d;
            border-radius: 6px;
            font-size: 11px;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s;
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
        }}
        
        .tooltip strong {{
            color: #58a6ff;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Data Flow Graph - MCP Crawl4AI RAG</h1>
            <div class="info">
                Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 
                {len(nodes_list)} nodes | {len(links)} connections
            </div>
            
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #58a6ff;"></div>
                    <span>File</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #a371f7;"></div>
                    <span>Class</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #8cc85f;"></div>
                    <span>Method</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #f97583;"></div>
                    <span>Import</span>
                </div>
                <div class="legend-item">
                    <span style="color: #8b949e;">→ Data Flow Direction</span>
                </div>
            </div>
        </div>
        
        <svg id="graph"></svg>
        <div class="tooltip"></div>
    </div>

    <script>
        const data = {{
            nodes: {json.dumps(nodes_list)},
            links: {json.dumps(links)}
        }};
        
        const svg = d3.select("#graph");
        const container = document.getElementById("graph");
        const width = container.clientWidth;
        const height = container.clientHeight;
        
        svg.attr("width", width).attr("height", height);
        
        // Color scheme for dark theme
        const colors = {{
            file: "#58a6ff",
            class: "#a371f7",
            method: "#8cc85f",
            import: "#f97583",
            function: "#ffa657"
        }};
        
        const tooltip = d3.select(".tooltip");
        
        // Create arrow markers
        svg.append("defs").selectAll("marker")
            .data(["arrow", "arrow-dashed"])
            .join("marker")
            .attr("id", d => d)
            .attr("viewBox", "0 -5 10 10")
            .attr("refX", 20)
            .attr("refY", 0)
            .attr("markerWidth", 8)
            .attr("markerHeight", 8)
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M0,-5L10,0L0,5")
            .attr("fill", "#8b949e");
        
        // Create simulation with directional force
        const simulation = d3.forceSimulation(data.nodes)
            .force("link", d3.forceLink(data.links).id(d => d.id).distance(80))
            .force("charge", d3.forceManyBody().strength(-400))
            .force("x", d3.forceX(d => width * (0.2 + d.level * 0.3)).strength(0.3))
            .force("y", d3.forceY(height / 2).strength(0.1))
            .force("collision", d3.forceCollide().radius(25));
        
        // Create container groups
        const g = svg.append("g");
        
        // Create links with arrows
        const link = g.append("g")
            .selectAll("line")
            .data(data.links)
            .join("line")
            .attr("stroke", d => d.dashed ? "#30363d" : "#484f58")
            .attr("stroke-opacity", 0.8)
            .attr("stroke-width", d => d.type === 'imports' ? 1 : 2)
            .attr("stroke-dasharray", d => d.dashed ? "5,5" : null)
            .attr("marker-end", d => d.arrow ? (d.dashed ? "url(#arrow-dashed)" : "url(#arrow)") : null);
        
        // Create nodes
        const node = g.append("g")
            .selectAll("g")
            .data(data.nodes)
            .join("g")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
        
        // Add circles for nodes
        node.append("circle")
            .attr("r", d => d.type === 'file' ? 8 : d.type === 'class' ? 7 : 5)
            .attr("fill", d => colors[d.type] || "#8b949e")
            .attr("stroke", "#0d1117")
            .attr("stroke-width", 2);
        
        // Add labels
        node.append("text")
            .text(d => d.label)
            .attr("x", 12)
            .attr("y", 4)
            .style("font-size", "10px")
            .style("fill", "#c9d1d9");
        
        // Tooltip interactions
        node.on("mouseover", function(event, d) {{
            tooltip.transition().duration(200).style("opacity", .95);
            tooltip.html(`
                <strong>${{d.type.toUpperCase()}}</strong><br/>
                ${{d.label}}<br/>
                Level: ${{d.level}}
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");
        }})
        .on("mouseout", function(d) {{
            tooltip.transition().duration(500).style("opacity", 0);
        }});
        
        // Zoom functionality
        const zoom = d3.zoom()
            .scaleExtent([0.5, 3])
            .on("zoom", (event) => {{
                g.attr("transform", event.transform);
            }});
        
        svg.call(zoom);
        
        // Simulation tick
        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
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
        
        # Save to visualizations directory
        vis_dir = Path(".crawl4ai/visualizations")
        vis_dir.mkdir(parents=True, exist_ok=True)
        
        html_file = vis_dir / "mcp-crawl4ai-rag_dataflow_graph.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n=== Data Flow Visualization Created ===")
        print(f"HTML file: {html_file.absolute()}")
        print(f"Nodes: {len(nodes_list)}")
        print(f"Links: {len(links)}")
        print(f"\nTo view: file://{html_file.absolute()}")
        
    except Exception as e:
        logger.error(f"Error creating visualization: {e}")
        raise
    finally:
        await extractor.close()

if __name__ == "__main__":
    asyncio.run(main())