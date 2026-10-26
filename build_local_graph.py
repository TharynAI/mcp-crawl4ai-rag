#!/usr/bin/env python3
"""
Build knowledge graph of the local mcp-crawl4ai-rag repository
"""

import asyncio
import logging
import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

async def main():
    """Build knowledge graph using the GitHub repository URL"""
    load_dotenv()
    
    # Import after setting up path
    import sys
    sys.path.insert(0, str(Path(__file__).parent / "knowledge_graphs"))
    from parse_repo_into_neo4j import DirectNeo4jExtractor
    
    neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
    neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
    neo4j_password = os.environ.get('NEO4J_PASSWORD', 'neo4j123')
    
    logger.info("Building knowledge graph for mcp-crawl4ai-rag")
    logger.info(f"Neo4j URI: {neo4j_uri}")
    
    extractor = DirectNeo4jExtractor(neo4j_uri, neo4j_user, neo4j_password)
    
    try:
        await extractor.initialize()
        
        # Use the GitHub URL to analyze this repository
        repo_url = "https://github.com/coleam00/mcp-crawl4ai-rag.git"
        logger.info(f"Analyzing repository from: {repo_url}")
        
        await extractor.analyze_repository(repo_url)
        
        # Query the results
        print("\n=== Repository Analysis Complete ===")
        
        # Get basic stats
        repo_name = "mcp-crawl4ai-rag"
        
        # List files
        results = await extractor.search_graph("files_in_repository", repo_name=repo_name)
        print(f"Python files analyzed: {len(results)}")
        
        # List main source files
        src_files = [r for r in results if 'src/' in r.get('file', '') or 'knowledge_graphs/' in r.get('file', '')]
        print(f"\nMain source files ({len(src_files)}):")
        for result in src_files[:15]:  # Show first 15
            print(f"- {result['file']}")
        
        # List classes
        results = await extractor.search_graph("classes_in_repository", repo_name=repo_name)
        print(f"\nClasses found ({len(results)}):")
        for result in results[:10]:  # Show first 10
            print(f"- {result['class_name']} (in {result['file']})")
        
        print(f"\nKnowledge graph built successfully!")
        print(f"You can view it at: http://localhost:7474")
        print(f"Login with: neo4j / neo4j123")
        
    except Exception as e:
        logger.error(f"Error building knowledge graph: {e}")
        raise
    finally:
        await extractor.close()

if __name__ == "__main__":
    asyncio.run(main())