#!/usr/bin/env python3
"""
Unreal Engine 5.5.4 LastMilePasses Plugin Analysis Plan
======================================================

This script systematically builds knowledge graphs for the specific UE modules
needed to implement the LastMilePasses plugin with focus on:
- Scene View Extensions
- Post-processing Pipeline
- Component System (UStaticMeshComponent)
- Material System
- Subsystems
- Buffer Visualization
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import List, Dict, Set
sys.path.insert(0, str(Path(__file__).parent / "knowledge_graphs"))

from parse_repo_into_neo4j import DirectNeo4jExtractor

class UELastMilePassesAnalyzer:
    def __init__(self, ue_path: str = "/mnt/e/GitHub/UE554-match"):
        self.ue_path = Path(ue_path)
        self.runtime_path = self.ue_path / "Engine/Source/Runtime"
        self.editor_path = self.ue_path / "Engine/Source/Editor"
        
        # Neo4j connection
        self.neo4j_uri = os.environ.get('NEO4J_URI', 'bolt://localhost:7687')
        self.neo4j_user = os.environ.get('NEO4J_USER', 'neo4j')
        self.neo4j_password = os.environ.get('NEO4J_PASSWORD', 'neo4j123')
        
        # Critical modules for LastMilePasses plugin
        self.critical_modules = {
            "core_foundation": [
                "Core",
                "CoreUObject", 
                "ApplicationCore",
                "Projects"
            ],
            "rendering_pipeline": [
                "RenderCore",
                "Renderer", 
                "RHI",
                "Engine",  # Contains SceneView, PostProcess
                "MaterialShaderQualitySettings"
            ],
            "component_system": [
                "Engine",  # UActorComponent, UPrimitiveComponent, UStaticMeshComponent
                "CoreUObject"  # UObject base classes
            ],
            "editor_integration": [
                "UnrealEd",
                "ToolMenus",
                "EditorStyle",
                "PropertyEditor"
            ]
        }
        
        # Key classes to verify exist in knowledge graph
        self.verification_classes = {
            "SceneViewExtension": ["FSceneViewExtensionBase", "ISceneViewExtension"],
            "PostProcessing": ["FPostProcessingInputs", "FPostProcessPassParameters"],
            "Components": ["UStaticMeshComponent", "UPrimitiveComponent", "UActorComponent"],
            "Materials": ["UMaterial", "FMaterial", "FMaterialRenderProxy"],
            "Subsystems": ["UEngineSubsystem", "UWorldSubsystem"],
            "RenderTargets": ["FRenderTarget", "FTextureRenderTarget2D"],
            "Settings": ["UDeveloperSettings"],
            "BufferVisualization": ["FBufferVisualizationData"]
        }

    async def analyze_critical_modules(self):
        """Analyze the modules critical for LastMilePasses plugin development."""
        extractor = DirectNeo4jExtractor(self.neo4j_uri, self.neo4j_user, self.neo4j_password)
        
        try:
            await extractor.initialize()
            
            # Clear existing UE data
            print("🧹 Clearing existing UE analysis data...")
            await extractor.driver.execute_query("MATCH (n {project: 'UE554_LastMilePasses'}) DETACH DELETE n")
            
            for phase_name, modules in self.critical_modules.items():
                print(f"\n🔍 Analyzing {phase_name.upper()} phase...")
                
                for module_name in modules:
                    module_path = self.runtime_path / module_name
                    if not module_path.exists():
                        # Try editor path
                        module_path = self.editor_path / module_name
                        if not module_path.exists():
                            print(f"⚠️  Module not found: {module_name}")
                            continue
                    
                    print(f"   📁 Processing module: {module_name}")
                    await self.analyze_module(extractor, module_name, module_path, phase_name)
            
            # Verify critical classes exist
            await self.verify_critical_classes(extractor)
            
            # Generate specific queries for LastMilePasses development
            await self.generate_development_queries(extractor)
            
        finally:
            await extractor.close()

    async def analyze_module(self, extractor: DirectNeo4jExtractor, module_name: str, 
                           module_path: Path, phase: str):
        """Analyze a specific UE module."""
        files_to_analyze = []
        
        # Get header files (focus on Public first, then Private)
        public_path = module_path / "Public"
        private_path = module_path / "Private"
        classes_path = module_path / "Classes"
        
        for search_path in [public_path, classes_path, private_path]:
            if search_path.exists():
                for header_file in search_path.rglob("*.h"):
                    # Skip generated files
                    if ".generated.h" not in str(header_file):
                        files_to_analyze.append(header_file)
        
        print(f"      Found {len(files_to_analyze)} header files")
        
        # Process files in batches
        batch_size = 50
        for i in range(0, len(files_to_analyze), batch_size):
            batch = files_to_analyze[i:i + batch_size]
            await self.process_file_batch(extractor, batch, module_name, phase)

    async def process_file_batch(self, extractor: DirectNeo4jExtractor, files: List[Path], 
                                module_name: str, phase: str):
        """Process a batch of files."""
        for file_path in files:
            try:
                # Read file content
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Extract classes, functions, and relationships
                await self.extract_file_elements(extractor, file_path, content, module_name, phase)
                
            except Exception as e:
                print(f"         ⚠️  Error processing {file_path.name}: {str(e)}")

    async def extract_file_elements(self, extractor: DirectNeo4jExtractor, file_path: Path, 
                                  content: str, module_name: str, phase: str):
        """Extract UE-specific elements from file content."""
        relative_path = str(file_path).replace(str(self.ue_path), "")
        
        # Create file node
        file_query = """
        MERGE (f:File {path: $path, project: 'UE554_LastMilePasses'})
        SET f.name = $name,
            f.module = $module,
            f.phase = $phase,
            f.size = $size,
            f.extension = $extension
        """
        
        await extractor.driver.execute_query(file_query, {
            'path': relative_path,
            'name': file_path.name,
            'module': module_name,
            'phase': phase,
            'size': len(content),
            'extension': file_path.suffix
        })
        
        # Extract UE classes (UCLASS, USTRUCT, UENUM)
        await self.extract_ue_classes(extractor, content, relative_path, module_name, phase)
        
        # Extract key function signatures
        await self.extract_key_functions(extractor, content, relative_path, module_name, phase)

    async def extract_ue_classes(self, extractor: DirectNeo4jExtractor, content: str, 
                                file_path: str, module_name: str, phase: str):
        """Extract UE class definitions with macro annotations."""
        import re
        
        # Pattern for UE classes
        class_patterns = [
            (r'UCLASS\([^)]*\)\s*class\s+(\w+_API\s+)?(\w+)\s*:\s*public\s+(\w+)', 'UCLASS'),
            (r'USTRUCT\([^)]*\)\s*struct\s+(\w+_API\s+)?(\w+)', 'USTRUCT'),
            (r'UENUM\([^)]*\)\s*enum\s+class\s+(\w+)', 'UENUM'),
            (r'class\s+(\w+_API\s+)?(\w+)\s*:\s*public\s+(F\w+|I\w+|U\w+)', 'CLASS'),
            (r'struct\s+(\w+_API\s+)?(\w+)', 'STRUCT')
        ]
        
        for pattern, class_type in class_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                if class_type in ['UCLASS', 'USTRUCT', 'UENUM']:
                    class_name = match.group(2) if match.group(1) else match.group(1)
                    parent_class = match.group(3) if len(match.groups()) > 2 and match.group(3) else None
                else:
                    class_name = match.group(2) if match.group(1) else match.group(1)
                    parent_class = match.group(3) if len(match.groups()) > 2 else None
                
                if class_name and len(class_name) > 1:  # Valid class name
                    await self.create_class_node(extractor, class_name, class_type, parent_class, 
                                               file_path, module_name, phase)

    async def create_class_node(self, extractor: DirectNeo4jExtractor, class_name: str, 
                              class_type: str, parent_class: str, file_path: str, 
                              module_name: str, phase: str):
        """Create class node and relationships."""
        
        # Create class node
        class_query = """
        MERGE (c:Class {name: $name, project: 'UE554_LastMilePasses'})
        SET c.type = $type,
            c.module = $module,
            c.phase = $phase,
            c.file_path = $file_path,
            c.parent_class = $parent_class
        """
        
        await extractor.driver.execute_query(class_query, {
            'name': class_name,
            'type': class_type,
            'module': module_name,
            'phase': phase,
            'file_path': file_path,
            'parent_class': parent_class
        })
        
        # Create file -> class relationship
        file_class_query = """
        MATCH (f:File {path: $file_path, project: 'UE554_LastMilePasses'})
        MATCH (c:Class {name: $class_name, project: 'UE554_LastMilePasses'})
        MERGE (f)-[:DEFINES]->(c)
        """
        
        await extractor.driver.execute_query(file_class_query, {
            'file_path': file_path,
            'class_name': class_name
        })
        
        # Create inheritance relationship
        if parent_class and parent_class not in ['public', 'private', 'protected']:
            inheritance_query = """
            MATCH (child:Class {name: $child_name, project: 'UE554_LastMilePasses'})
            MERGE (parent:Class {name: $parent_name, project: 'UE554_LastMilePasses'})
            MERGE (child)-[:INHERITS]->(parent)
            """
            
            await extractor.driver.execute_query(inheritance_query, {
                'child_name': class_name,
                'parent_name': parent_class
            })

    async def extract_key_functions(self, extractor: DirectNeo4jExtractor, content: str, 
                                  file_path: str, module_name: str, phase: str):
        """Extract key function signatures relevant to LastMilePasses."""
        import re
        
        # Key functions for plugin development
        key_function_patterns = [
            r'(virtual\s+)?void\s+(\w*PostProcess\w*)\s*\([^)]*\)',
            r'(virtual\s+)?void\s+(\w*SceneView\w*)\s*\([^)]*\)',
            r'(virtual\s+)?void\s+(\w*Render\w*)\s*\([^)]*\)',
            r'(virtual\s+)?(\w+)\s+Get(\w+)\s*\([^)]*\)',
            r'UFUNCTION\([^)]*\)\s*[^;]*?(\w+)\s*\([^)]*\)'
        ]
        
        for pattern in key_function_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                function_name = None
                if 'PostProcess' in pattern or 'SceneView' in pattern or 'Render' in pattern:
                    function_name = match.group(2)
                elif 'Get' in pattern:
                    function_name = f"Get{match.group(3)}"
                elif 'UFUNCTION' in pattern:
                    function_name = match.group(1)
                
                if function_name and len(function_name) > 2:
                    await self.create_function_node(extractor, function_name, file_path, 
                                                  module_name, phase)

    async def create_function_node(self, extractor: DirectNeo4jExtractor, function_name: str, 
                                 file_path: str, module_name: str, phase: str):
        """Create function node."""
        function_query = """
        MERGE (func:Function {name: $name, file_path: $file_path, project: 'UE554_LastMilePasses'})
        SET func.module = $module,
            func.phase = $phase
        """
        
        await extractor.driver.execute_query(function_query, {
            'name': function_name,
            'file_path': file_path,
            'module': module_name,
            'phase': phase
        })

    async def verify_critical_classes(self, extractor: DirectNeo4jExtractor):
        """Verify that critical classes for LastMilePasses exist in the knowledge graph."""
        print("\n🔍 Verifying critical classes for LastMilePasses development...")
        
        verification_results = {}
        
        for category, classes in self.verification_classes.items():
            found_classes = []
            missing_classes = []
            
            for class_name in classes:
                query = """
                MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
                WHERE c.name CONTAINS $class_name
                RETURN c.name, c.module, c.phase
                LIMIT 5
                """
                
                result = await extractor.driver.execute_query(query, {'class_name': class_name})
                
                if result.records:
                    found_classes.extend([dict(record) for record in result.records])
                    print(f"   ✅ Found {class_name}: {[r['c.name'] for r in result.records]}")
                else:
                    missing_classes.append(class_name)
                    print(f"   ❌ Missing {class_name}")
            
            verification_results[category] = {
                'found': found_classes,
                'missing': missing_classes
            }
        
        return verification_results

    async def generate_development_queries(self, extractor: DirectNeo4jExtractor):
        """Generate specific queries for LastMilePasses plugin development."""
        print("\n📝 Generating development queries for LastMilePasses...")
        
        queries = {
            "scene_view_extensions": """
            MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
            WHERE c.name CONTAINS 'SceneView' OR c.name CONTAINS 'ViewExtension'
            RETURN c.name, c.module, c.file_path, c.parent_class
            ORDER BY c.name
            """,
            
            "post_process_classes": """
            MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
            WHERE c.name CONTAINS 'PostProcess' OR c.name CONTAINS 'PostProcessing'
            RETURN c.name, c.module, c.file_path, c.parent_class
            ORDER BY c.name
            """,
            
            "component_hierarchy": """
            MATCH (child:Class)-[:INHERITS*]->(parent:Class {name: 'UActorComponent', project: 'UE554_LastMilePasses'})
            WHERE child.project = 'UE554_LastMilePasses'
            RETURN child.name, parent.name, child.module
            ORDER BY child.name
            """,
            
            "static_mesh_component": """
            MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
            WHERE c.name CONTAINS 'StaticMesh' AND c.name CONTAINS 'Component'
            OPTIONAL MATCH (c)-[:INHERITS]->(parent:Class)
            RETURN c.name, c.module, c.file_path, parent.name as parent_class
            """,
            
            "material_classes": """
            MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
            WHERE c.name CONTAINS 'Material' AND NOT c.name CONTAINS 'Interface'
            RETURN c.name, c.module, c.file_path, c.type
            ORDER BY c.name
            """,
            
            "subsystem_classes": """
            MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
            WHERE c.name CONTAINS 'Subsystem'
            RETURN c.name, c.module, c.file_path, c.parent_class
            ORDER BY c.name
            """,
            
            "render_target_classes": """
            MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
            WHERE c.name CONTAINS 'RenderTarget' OR c.name CONTAINS 'Texture'
            RETURN c.name, c.module, c.file_path
            ORDER BY c.name
            """,
            
            "developer_settings": """
            MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
            WHERE c.name CONTAINS 'Settings' OR c.name CONTAINS 'Config'
            RETURN c.name, c.module, c.file_path
            ORDER BY c.name
            """
        }
        
        print("\n🔍 Executing development queries...")
        results = {}
        
        for query_name, query in queries.items():
            try:
                result = await extractor.driver.execute_query(query)
                results[query_name] = [dict(record) for record in result.records]
                print(f"   📊 {query_name}: {len(results[query_name])} results")
            except Exception as e:
                print(f"   ❌ Error in {query_name}: {str(e)}")
                results[query_name] = []
        
        # Save results for agent use
        await self.save_development_results(results)
        
        return results

    async def save_development_results(self, results: Dict):
        """Save development query results for agent consumption."""
        import json
        
        output_file = Path(".crawl4ai/ue_lastmilepasses_analysis.json")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"📄 Development results saved to: {output_file}")

    async def generate_agent_instructions(self):
        """Generate specific instructions for coding agents working on LastMilePasses."""
        
        instructions = """
# LastMilePasses Plugin Development - Agent Instructions

## Knowledge Graph Analysis Complete ✅

The UE 5.5.4 engine has been analyzed with focus on LastMilePasses plugin requirements.

### Available Queries for Plugin Development

Use these specific queries in your development workflow:

#### 1. Scene View Extension Research
```cypher
MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
WHERE c.name CONTAINS 'SceneView' OR c.name CONTAINS 'ViewExtension'
RETURN c.name, c.module, c.file_path, c.parent_class
ORDER BY c.name
```

#### 2. Post-Processing Pipeline Classes
```cypher
MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
WHERE c.name CONTAINS 'PostProcess' OR c.name CONTAINS 'PostProcessing'
RETURN c.name, c.module, c.file_path, c.parent_class
ORDER BY c.name
```

#### 3. Component System Hierarchy
```cypher
MATCH (child:Class)-[:INHERITS*]->(parent:Class {name: 'UActorComponent', project: 'UE554_LastMilePasses'})
WHERE child.project = 'UE554_LastMilePasses'
RETURN child.name, parent.name, child.module
ORDER BY child.name
```

#### 4. StaticMeshComponent Analysis
```cypher
MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
WHERE c.name CONTAINS 'StaticMesh' AND c.name CONTAINS 'Component'
OPTIONAL MATCH (c)-[:INHERITS]->(parent:Class)
RETURN c.name, c.module, c.file_path, parent.name as parent_class
```

#### 5. Material System Classes
```cypher
MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
WHERE c.name CONTAINS 'Material' AND NOT c.name CONTAINS 'Interface'
RETURN c.name, c.module, c.file_path, c.type
ORDER BY c.name
```

#### 6. Subsystem Classes
```cypher
MATCH (c:Class {project: 'UE554_LastMilePasses'}) 
WHERE c.name CONTAINS 'Subsystem'
RETURN c.name, c.module, c.file_path, c.parent_class
ORDER BY c.name
```

### Module Organization

The analysis covers these critical modules:

**Core Foundation**: Core, CoreUObject, ApplicationCore, Projects
**Rendering Pipeline**: RenderCore, Renderer, RHI, Engine, MaterialShaderQualitySettings  
**Component System**: Engine (UActorComponent hierarchy), CoreUObject
**Editor Integration**: UnrealEd, ToolMenus, EditorStyle, PropertyEditor

### Development Workflow

1. **Research Phase**: Use the queries above to understand existing patterns
2. **Design Phase**: Model your components after existing UE patterns
3. **Implementation Phase**: Follow UE naming conventions and inheritance patterns
4. **Validation Phase**: Test against the verification classes listed in the spec

### Key Files to Reference

Use the knowledge graph to find:
- SceneViewExtension base classes and examples
- PostProcessing pass implementations  
- StaticMeshComponent flag manipulation patterns
- Subsystem registration and lifecycle
- Material validation and property checking
- Developer settings configuration patterns

### Next Steps

1. Query the knowledge graph for specific implementation patterns
2. Use the found classes as templates for your LastMilePasses implementation
3. Follow the inheritance and composition patterns discovered
4. Validate your implementation against UE coding standards found in the analysis

The knowledge graph contains comprehensive information about UE 5.5.4's architecture
specifically focused on the systems you'll need for LastMilePasses plugin development.
"""
        
        output_file = Path(".crawl4ai/UE_LASTMILEPASSES_AGENT_INSTRUCTIONS.md")
        with open(output_file, 'w') as f:
            f.write(instructions)
        
        print(f"📋 Agent instructions saved to: {output_file}")

async def main():
    """Main execution function."""
    analyzer = UELastMilePassesAnalyzer()
    
    print("🚀 Starting UE 5.5.4 LastMilePasses Analysis...")
    print(f"📂 Engine Path: {analyzer.ue_path}")
    print(f"🔗 Neo4j: {analyzer.neo4j_uri}")
    
    # Run the analysis
    await analyzer.analyze_critical_modules()
    
    # Generate agent instructions
    await analyzer.generate_agent_instructions()
    
    print("\n✅ UE LastMilePasses analysis complete!")
    print("📊 Knowledge graph ready for plugin development")
    print("📋 Agent instructions generated")

if __name__ == "__main__":
    asyncio.run(main())