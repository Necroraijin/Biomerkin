#!/usr/bin/env python3
"""
Lambda function packaging script for Biomerkin deployment
Creates deployment packages with dependencies
"""

import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LambdaPackager:
    """Packages Lambda functions with dependencies for deployment"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.lambda_source = self.project_root / "lambda_functions"
        self.biomerkin_source = self.project_root / "biomerkin"
        self.output_dir = self.project_root / "dist"
        
        # Ensure output directory exists
        self.output_dir.mkdir(exist_ok=True)
    
    def install_dependencies(self, temp_dir: Path) -> bool:
        """Install Python dependencies in temporary directory"""
        logger.info("Installing dependencies...")
        
        try:
            # Copy requirements.txt to temp directory
            requirements_file = self.project_root / "requirements.txt"
            if requirements_file.exists():
                shutil.copy2(requirements_file, temp_dir)
                
                # Install dependencies
                result = subprocess.run([
                    'pip', 'install', '-r', 'requirements.txt', '-t', str(temp_dir)
                ], cwd=temp_dir, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Dependency installation failed: {result.stderr}")
                    return False
                
                logger.info("Dependencies installed successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {str(e)}")
            return False
    
    def copy_source_code(self, temp_dir: Path) -> bool:
        """Copy source code to temporary directory"""
        logger.info("Copying source code...")
        
        try:
            # Copy biomerkin package
            if self.biomerkin_source.exists():
                shutil.copytree(
                    self.biomerkin_source,
                    temp_dir / "biomerkin",
                    ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.pyo')
                )
            
            # Copy lambda functions
            if self.lambda_source.exists():
                for lambda_file in self.lambda_source.glob("*.py"):
                    shutil.copy2(lambda_file, temp_dir)
            
            logger.info("Source code copied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error copying source code: {str(e)}")
            return False
    
    def create_deployment_package(self, temp_dir: Path, package_name: str) -> bool:
        """Create ZIP deployment package"""
        logger.info(f"Creating deployment package: {package_name}")
        
        try:
            package_path = self.output_dir / f"{package_name}.zip"
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(temp_dir):
                    # Skip __pycache__ directories
                    dirs[:] = [d for d in dirs if d != '__pycache__']
                    
                    for file in files:
                        if not file.endswith(('.pyc', '.pyo')):
                            file_path = Path(root) / file
                            arcname = file_path.relative_to(temp_dir)
                            zipf.write(file_path, arcname)
            
            logger.info(f"Package created: {package_path}")
            logger.info(f"Package size: {package_path.stat().st_size / 1024 / 1024:.2f} MB")
            return True
            
        except Exception as e:
            logger.error(f"Error creating deployment package: {str(e)}")
            return False
    
    def package_all_functions(self) -> bool:
        """Package all Lambda functions"""
        logger.info("Starting Lambda function packaging...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Install dependencies
                if not self.install_dependencies(temp_path):
                    return False
                
                # Copy source code
                if not self.copy_source_code(temp_path):
                    return False
                
                # Create deployment package
                if not self.create_deployment_package(temp_path, "biomerkin-lambda-package"):
                    return False
            
            logger.info("All Lambda functions packaged successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Packaging failed: {str(e)}")
            return False
    
    def create_layer_package(self) -> bool:
        """Create Lambda layer package for common dependencies"""
        logger.info("Creating Lambda layer package...")
        
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                python_dir = temp_path / "python"
                python_dir.mkdir()
                
                # Install only external dependencies for layer
                layer_requirements = [
                    "boto3>=1.28.0",
                    "biopython>=1.81",
                    "requests>=2.31.0",
                    "numpy>=1.24.0",
                    "pandas>=2.0.0"
                ]
                
                for requirement in layer_requirements:
                    result = subprocess.run([
                        'pip', 'install', requirement, '-t', str(python_dir)
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        logger.warning(f"Failed to install {requirement}: {result.stderr}")
                
                # Create layer package
                if not self.create_deployment_package(temp_path, "biomerkin-layer"):
                    return False
            
            logger.info("Lambda layer package created successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Layer packaging failed: {str(e)}")
            return False


def main():
    """Main entry point"""
    packager = LambdaPackager()
    
    # Package Lambda functions
    if not packager.package_all_functions():
        return False
    
    # Create Lambda layer
    if not packager.create_layer_package():
        return False
    
    return True


if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)