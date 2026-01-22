"""Enhanced Terraform parser with TerraVision integration."""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Add tools to path for imports
repo_root = Path(__file__).resolve().parents[1]
tools_dir = repo_root / "tools"
if str(tools_dir) not in sys.path:
    sys.path.insert(0, str(tools_dir))

try:
    from terravision_integration import integrate_terravision_analysis, TerraVisionConfig
    TERRAVISION_AVAILABLE = True
except ImportError:
    TERRAVISION_AVAILABLE = False
    print("⚠️  TerraVision integration not available (Docker required)")

try:
    import hcl2
    HCL2_AVAILABLE = True
except ImportError:
    HCL2_AVAILABLE = False


class EnhancedTerraformParser:
    """Enhanced Terraform parser with TerraVision and HCL2 fallback."""
    
    def __init__(self, enable_terravision: bool = True, mock_credentials: bool = True):
        self.enable_terravision = enable_terravision and TERRAVISION_AVAILABLE
        self.mock_credentials = mock_credentials
        self.use_hcl2_fallback = HCL2_AVAILABLE
    
    def parse_terraform_directory(self, terraform_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str]], Dict[str, Any]]:
        """
        Parse Terraform directory with enhanced analysis.
        
        Returns:
            Tuple of (resources, dependencies, metadata)
        """
        if self.enable_terravision:
            try:
                # Try TerraVision first for enhanced analysis
                config = TerraVisionConfig() if self.mock_credentials else None
                analysis = integrate_terravision_analysis(terraform_dir, config)
                
                resources = analysis.get("resources", {})
                dependencies = analysis.get("dependencies", [])
                metadata = analysis.get("metadata", {})
                
                print(f"✅ TerraVision analysis successful")
                return resources, dependencies, metadata
                
            except Exception as e:
                print(f"⚠️  TerraVision analysis failed: {e}")
                print("   Falling back to HCL2 parsing...")
        
        # Fallback to HCL2 parsing
        if self.use_hcl2_fallback:
            try:
                resources, dependencies = self._parse_with_hcl2(terraform_dir)
                metadata = {
                    "source": "hcl2_fallback",
                    "complexity_score": len(resources) + len(dependencies),
                    "cloud_providers": self._extract_providers_from_resources(resources),
                    "resource_types": list(set(r.get("type", "unknown") for r in resources.values()))
                }
                
                print(f"✅ HCL2 fallback parsing successful")
                return resources, dependencies, metadata
                
            except Exception as e:
                print(f"❌ HCL2 parsing failed: {e}")
        
        # Last resort - basic file parsing
        return self._parse_basic(terraform_dir)
    
    def _parse_with_hcl2(self, terraform_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str]]]:
        """Parse using HCL2 library."""
        resources = {}
        dependencies = []
        
        for tf_file in terraform_dir.glob("*.tf"):
            try:
                content = tf_file.read_text()
                parsed = hcl2.loads(content)
                
                if "resource" in parsed:
                    for resource_type, resource_configs in parsed["resource"].items():
                        for resource_name, resource_config in resource_configs.items():
                            full_name = f"{resource_type}.{resource_name}"
                            resources[full_name] = {
                                "type": resource_type,
                                "config": resource_config,
                                "source_file": tf_file.name
                            }
                            
                            # Extract dependencies from resource references
                            deps = self._extract_dependencies_from_config(resource_config)
                            for dep in deps:
                                dependencies.append((full_name, dep))
                                
            except Exception:
                continue
        
        return resources, dependencies
    
    def _extract_dependencies_from_config(self, config: Any) -> List[str]:
        """Extract resource dependencies from configuration."""
        dependencies = []
        
        if isinstance(config, dict):
            for key, value in config.items():
                if isinstance(value, str) and "${" in value:
                    # Extract resource references from interpolation
                    import re
                    refs = re.findall(r'\${([^}]+)}', value)
                    for ref in refs:
                        if '.' in ref and not ref.startswith('var.'):
                            # This looks like a resource reference
                            resource_ref = ref.split('.')[0] + '.' + ref.split('.')[1]
                            dependencies.append(resource_ref)
                elif isinstance(value, (dict, list)):
                    dependencies.extend(self._extract_dependencies_from_config(value))
        
        elif isinstance(config, list):
            for item in config:
                dependencies.extend(self._extract_dependencies_from_config(item))
        
        return dependencies
    
    def _extract_providers_from_resources(self, resources: Dict[str, Dict[str, Any]]) -> List[str]:
        """Extract cloud providers from resource types."""
        providers = set()
        for resource_data in resources.values():
            resource_type = resource_data.get("type", "")
            if resource_type.startswith("aws_"):
                providers.add("aws")
            elif resource_type.startswith("azurerm_"):
                providers.add("azure")
            elif resource_type.startswith("google_"):
                providers.add("gcp")
            elif resource_type.startswith("oci_"):
                providers.add("oci")
            elif resource_type.startswith("ibm_"):
                providers.add("ibm")
        return list(providers)
    
    def _parse_basic(self, terraform_dir: Path) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str]], Dict[str, Any]]:
        """Basic parsing as last resort."""
        resources = {}
        dependencies = []
        
        for tf_file in terraform_dir.glob("*.tf"):
            try:
                content = tf_file.read_text()
                # Simple regex-based resource extraction
                import re
                
                # Find resource blocks
                resource_pattern = r'resource\s+"([^"]+)"\s+"([^"]+)"'
                matches = re.findall(resource_pattern, content)
                
                for resource_type, resource_name in matches:
                    full_name = f"{resource_type}.{resource_name}"
                    resources[full_name] = {
                        "type": resource_type,
                        "config": {},
                        "source_file": tf_file.name
                    }
                    
            except Exception:
                continue
        
        metadata = {
            "source": "basic_regex",
            "complexity_score": len(resources),
            "cloud_providers": self._extract_providers_from_resources(resources),
            "resource_types": list(set(r.get("type", "unknown") for r in resources.values())),
            "warning": "Basic parsing - limited accuracy"
        }
        
        return resources, dependencies, metadata


def parse_terraform_enhanced(terraform_dir: Path, 
                           enable_terravision: bool = True,
                           mock_credentials: bool = True) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str]], Dict[str, Any]]:
    """
    Enhanced Terraform parsing with TerraVision integration.
    
    Args:
        terraform_dir: Directory containing Terraform files
        enable_terravision: Whether to use TerraVision if available
        mock_credentials: Whether to use mock credentials for TerraVision
        
    Returns:
        Tuple of (resources, dependencies, metadata)
    """
    parser = EnhancedTerraformParser(enable_terravision, mock_credentials)
    return parser.parse_terraform_directory(terraform_dir)


# Integration function for existing workflow
def enhance_terraform_parsing(terraform_files: List[Path], 
                          enable_terravision: bool = True,
                          mock_credentials: bool = True) -> Tuple[Dict[str, Dict[str, Any]], List[Tuple[str, str]], Dict[str, Any]]:
    """
    Enhanced parsing for multiple Terraform files.
    
    Args:
        terraform_files: List of Terraform files to parse
        enable_terravision: Whether to use TerraVision analysis
        mock_credentials: Whether to use mock credentials
        
    Returns:
        Tuple of (all_resources, all_dependencies, combined_metadata)
    """
    all_resources = {}
    all_dependencies = []
    all_providers = set()
    all_resource_types = set()
    analysis_sources = []
    total_complexity = 0
    
    # Group files by directory
    directories = {}
    for tf_file in terraform_files:
        tf_dir = tf_file.parent
        if tf_dir not in directories:
            directories[tf_dir] = []
        directories[tf_dir].append(tf_file)
    
    # Parse each directory
    for tf_dir, files in directories.items():
        resources, dependencies, metadata = parse_terraform_enhanced(
            tf_dir, enable_terravision, mock_credentials
        )
        
        # Add directory prefix to resource names to avoid conflicts
        dir_prefix = tf_dir.name.replace("-", "_")
        for res_name, res_data in resources.items():
            prefixed_name = f"{dir_prefix}_{res_name}"
            all_resources[prefixed_name] = res_data
        
        # Add directory prefix to dependencies
        for source, target in dependencies:
            prefixed_source = f"{dir_prefix}_{source}"
            prefixed_target = f"{dir_prefix}_{target}"
            all_dependencies.append((prefixed_source, prefixed_target))
        
        # Collect metadata
        all_providers.update(metadata.get("cloud_providers", []))
        all_resource_types.update(metadata.get("resource_types", []))
        analysis_sources.append(metadata.get("source", "unknown"))
        total_complexity += metadata.get("complexity_score", 0)
    
    combined_metadata = {
        "source": "enhanced_parser",
        "analysis_sources": analysis_sources,
        "complexity_score": total_complexity,
        "cloud_providers": list(all_providers),
        "resource_types": list(all_resource_types),
        "directories_parsed": len(directories),
        "files_parsed": len(terraform_files)
    }
    
    print(f"🔍 Enhanced parsing complete:")
    print(f"   Directories: {combined_metadata['directories_parsed']}")
    print(f"   Files: {combined_metadata['files_parsed']}")
    print(f"   Resources: {len(all_resources)}")
    print(f"   Dependencies: {len(all_dependencies)}")
    print(f"   Providers: {', '.join(combined_metadata['cloud_providers'])}")
    print(f"   Analysis methods: {', '.join(combined_metadata['analysis_sources'])}")
    
    return all_resources, all_dependencies, combined_metadata
