#!/usr/bin/env python3
"""
UE 5.5.4 Core Analysis - Phase 1: Critical Classes Only
=====================================================

Focus on the exact classes and functions mentioned in the LastMilePasses specification.
This creates a targeted knowledge graph for immediate plugin development needs.
"""

import asyncio
import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set
sys.path.insert(0, str(Path(__file__).parent / "knowledge_graphs"))

from parse_repo_into_neo4j import DirectNeo4jExtractor

class UECoreAnalyzer:
    def __init__(self, ue_path: str = "/mnt/e/GitHub/UE554-match"):
        self.ue_path = Path(ue_path)
        self.runtime_path = self.ue_path / "Engine/Source/Runtime"
        
        # Neo4j connection
        self.neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD', 'neo4j123')
        
        # Target classes mentioned in LastMilePasses spec
        self.target_classes = {
            'SceneViewExtension': ['FSceneViewExtensionBase', 'ISceneViewExtension'],
            'PostProcessing': ['FPostProcessingInputs', 'FPostProcessPassParameters'],
            'Components': ['UStaticMeshComponent', 'UPrimitiveComponent', 'UActorComponent'],
            'Materials': ['UMaterial', 'FMaterial', 'FMaterialRenderProxy'], 
            'Subsystems': ['UEngineSubsystem', 'UWorldSubsystem'],
            'RenderTargets': ['FRenderTarget', 'FTextureRenderTarget2D'],
            'Settings': ['UDeveloperSettings']
        }

    async def analyze_target_classes(self):
        """Find and analyze only the target classes needed for LastMilePasses."""
        extractor = DirectNeo4jExtractor(self.neo4j_uri, self.neo4j_user, self.neo4j_password)
        
        try:
            await extractor.initialize()
            
            # Clear previous UE core analysis
            print("🧹 Clearing existing UE core analysis...")
            await extractor.driver.execute_query("MATCH (n {project: 'UE554_Core'}) DETACH DELETE n")
            
            print("🔍 Searching for target classes in UE codebase...")
            
            # Search for each target class
            found_classes = {}
            for category, class_names in self.target_classes.items():
                print(f"\n📂 Searching {category}...")
                found_classes[category] = []
                
                for class_name in class_names:
                    file_paths = await self.find_class_definition(class_name)
                    if file_paths:
                        print(f"   ✅ Found {class_name} in {len(file_paths)} files")
                        for file_path in file_paths:
                            await self.analyze_class_file(extractor, file_path, class_name, category)
                            found_classes[category].append({'class': class_name, 'file': str(file_path)})
                    else:
                        print(f"   ❌ {class_name} not found")
            
            # Generate quick validation queries
            await self.generate_quick_queries(extractor)
            
            return found_classes
            
        finally:
            await extractor.close()

    async def find_class_definition(self, class_name: str) -> List[Path]:
        """Find files that define the target class."""
        found_files = []
        
        # Search in Engine/Source/Runtime directories
        for module_dir in self.runtime_path.iterdir():
            if not module_dir.is_dir():
                continue
                
            # Search in Public, Private, Classes directories
            for subdir in ['Public', 'Private', 'Classes']:
                search_dir = module_dir / subdir
                if search_dir.exists():
                    for header_file in search_dir.rglob("*.h"):
                        if self.file_contains_class(header_file, class_name):
                            found_files.append(header_file)
                            
                # Limit search to avoid timeout - take first few matches
                if len(found_files) >= 3:
                    break
            
            if len(found_files) >= 3:
                break
        
        return found_files

    def file_contains_class(self, file_path: Path, class_name: str) -> bool:
        """Check if file contains the target class definition."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Look for class/struct declaration
            patterns = [
                rf'class\s+\w*\s*{re.escape(class_name)}\b',
                rf'struct\s+\w*\s*{re.escape(class_name)}\b',
                rf'UCLASS.*class\s+\w*\s*{re.escape(class_name)}\b',
                rf'USTRUCT.*struct\s+\w*\s*{re.escape(class_name)}\b'
            ]
            
            for pattern in patterns:
                if re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                    return True
                    
            return False
            
        except Exception:
            return False

    async def analyze_class_file(self, extractor: DirectNeo4jExtractor, file_path: Path, 
                                class_name: str, category: str):
        """Analyze a specific file containing a target class."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            print(f"      ⚠️  Error reading {file_path}: {e}")
            return
        
        relative_path = str(file_path).replace(str(self.ue_path), "")
        module_name = self.get_module_name(file_path)
        
        # Create file node
        file_query = """
        MERGE (f:File {path: $path, project: 'UE554_Core'})
        SET f.name = $name,
            f.module = $module,
            f.category = $category,
            f.size = $size
        """
        
        await extractor.driver.execute_query(file_query, {
            'path': relative_path,
            'name': file_path.name,
            'module': module_name,
            'category': category,
            'size': len(content)
        })
        
        # Extract the specific class and its methods
        await self.extract_class_details(extractor, content, class_name, relative_path, 
                                        module_name, category)

    def get_module_name(self, file_path: Path) -> str:
        """Extract module name from file path."""
        # Path format: .../Engine/Source/Runtime/ModuleName/...
        parts = file_path.parts
        runtime_idx = -1
        for i, part in enumerate(parts):
            if part == "Runtime":
                runtime_idx = i
                break
        
        if runtime_idx >= 0 and runtime_idx + 1 < len(parts):
            return parts[runtime_idx + 1]
        
        return "Unknown"

    async def extract_class_details(self, extractor: DirectNeo4jExtractor, content: str,
                                  target_class: str, file_path: str, module_name: str, 
                                  category: str):
        """Extract detailed information about the target class."""
        
        # Find class definition
        class_match = re.search(
            rf'(UCLASS.*?)?\s*(class|struct)\s+(\w+_API\s+)?({re.escape(target_class)})\s*[:\s]',
            content, re.MULTILINE | re.DOTALL
        )
        
        if not class_match:
            return
        
        # Extract parent class
        parent_match = re.search(
            rf'{re.escape(target_class)}\s*:\s*public\s+(\w+)',
            content, re.MULTILINE
        )
        parent_class = parent_match.group(1) if parent_match else None
        
        # Create class node
        class_query = """
        MERGE (c:Class {name: $name, project: 'UE554_Core'})
        SET c.module = $module,
            c.category = $category,
            c.file_path = $file_path,
            c.parent_class = $parent_class,
            c.is_target_class = true
        """
        
        await extractor.driver.execute_query(class_query, {
            'name': target_class,
            'module': module_name,
            'category': category,
            'file_path': file_path,
            'parent_class': parent_class
        })
        
        # Link file to class
        await extractor.driver.execute_query("""
        MATCH (f:File {path: $file_path, project: 'UE554_Core'})
        MATCH (c:Class {name: $class_name, project: 'UE554_Core'})
        MERGE (f)-[:DEFINES]->(c)
        """, {'file_path': file_path, 'class_name': target_class})
        
        # Extract key methods (focus on virtual functions)
        await self.extract_key_methods(extractor, content, target_class, file_path)

    async def extract_key_methods(self, extractor: DirectNeo4jExtractor, content: str,
                                 class_name: str, file_path: str):
        """Extract key virtual methods from the class."""
        
        # Find virtual methods (key for plugin development)
        virtual_methods = re.finditer(
            r'virtual\s+(\w+\s*\*?\s*&?\s*)(\w+)\s*\([^)]*\)(?:\s*override)?(?:\s*const)?(?:\s*=\s*0)?',
            content, re.MULTILINE
        )
        
        for match in virtual_methods:
            return_type = match.group(1).strip()
            method_name = match.group(2)
            
            if len(method_name) > 2:  # Valid method name
                method_query = """
                MERGE (m:Method {name: $name, class_name: $class_name, project: 'UE554_Core'})
                SET m.return_type = $return_type,
                    m.file_path = $file_path,
                    m.is_virtual = true
                """
                
                await extractor.driver.execute_query(method_query, {
                    'name': method_name,
                    'class_name': class_name,
                    'return_type': return_type,
                    'file_path': file_path
                })
                
                # Link class to method
                await extractor.driver.execute_query("""
                MATCH (c:Class {name: $class_name, project: 'UE554_Core'})
                MATCH (m:Method {name: $method_name, class_name: $class_name, project: 'UE554_Core'})
                MERGE (c)-[:HAS_METHOD]->(m)
                """, {'class_name': class_name, 'method_name': method_name})

    async def generate_quick_queries(self, extractor: DirectNeo4jExtractor):
        """Generate quick verification queries."""
        print("\n🔍 Running verification queries...")
        
        queries = {
            "Found Classes": """
            MATCH (c:Class {project: 'UE554_Core'})
            RETURN c.name, c.module, c.category
            ORDER BY c.category, c.name
            """,
            
            "Scene View Extensions": """
            MATCH (c:Class {project: 'UE554_Core'})
            WHERE c.name CONTAINS 'SceneView' OR c.name CONTAINS 'ViewExtension'
            OPTIONAL MATCH (c)-[:HAS_METHOD]->(m:Method)
            RETURN c.name, c.parent_class, collect(m.name) as methods
            """,
            
            "Component Hierarchy": """
            MATCH (c:Class {project: 'UE554_Core'})
            WHERE c.name CONTAINS 'Component'
            RETURN c.name, c.parent_class, c.module
            ORDER BY c.name
            """,
            
            "Virtual Methods": """
            MATCH (c:Class {project: 'UE554_Core'})-[:HAS_METHOD]->(m:Method {is_virtual: true})
            RETURN c.name, m.name, m.return_type
            ORDER BY c.name, m.name
            """
        }
        
        results = {}
        for query_name, query in queries.items():
            try:
                result = await extractor.driver.execute_query(query)
                count = len(result.records)
                results[query_name] = [dict(record) for record in result.records]
                print(f"   📊 {query_name}: {count} results")
                
                # Show first few results
                for i, record in enumerate(result.records[:3]):
                    print(f"      {i+1}. {dict(record)}")
                if count > 3:
                    print(f"      ... and {count-3} more")
                    
            except Exception as e:
                print(f"   ❌ Error in {query_name}: {str(e)}")
        
        # Save results
        import json
        output_file = Path(".crawl4ai/ue_core_analysis_results.json")
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n📄 Results saved to: {output_file}")

async def main():
    analyzer = UECoreAnalyzer()
    
    print("🚀 Starting UE 5.5.4 Core Analysis (Target Classes Only)")
    print(f"📂 Engine Path: {analyzer.ue_path}")
    
    found_classes = await analyzer.analyze_target_classes()
    
    print("\n✅ Core analysis complete!")
    print("\n📋 Summary of found classes:")
    for category, classes in found_classes.items():
        print(f"   {category}: {len(classes)} classes")
        for class_info in classes:
            print(f"      - {class_info['class']}")

if __name__ == "__main__":
    asyncio.run(main())