"""
Linter service for the Code Review Agent worker.
"""
import logging
import os
import tempfile
import subprocess
import json
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)

class LinterService:
    """Service for running language-specific linters."""
    
    def __init__(self):
        """Initialize the linter service."""
        self.supported_languages = {
            ".py": "python",
            ".js": "javascript",
            ".jsx": "javascript",
            ".ts": "typescript",
            ".tsx": "typescript",
            ".java": "java",
            ".cs": "csharp",
            ".go": "go",
        }
    
    def run_linters(self, diff: str) -> Dict[str, Any]:
        """
        Run linters on the code diff.
        
        Args:
            diff: The code diff
            
        Returns:
            A dictionary containing linter results for each language
        """
        try:
            # Parse the diff to extract file changes
            files = self._parse_diff(diff)
            
            # Group files by language
            files_by_language = self._group_files_by_language(files)
            
            # Run linters for each language
            results = {}
            
            for language, file_contents in files_by_language.items():
                if language == "python":
                    results["python"] = self._run_python_linters(file_contents)
                elif language == "javascript":
                    results["javascript"] = self._run_javascript_linters(file_contents)
                elif language == "typescript":
                    results["typescript"] = self._run_typescript_linters(file_contents)
                elif language == "java":
                    results["java"] = self._run_java_linters(file_contents)
                elif language == "csharp":
                    results["csharp"] = self._run_csharp_linters(file_contents)
                elif language == "go":
                    results["go"] = self._run_go_linters(file_contents)
            
            return results
        
        except Exception as e:
            logger.exception(f"Error running linters: {str(e)}")
            return {}
    
    def _parse_diff(self, diff: str) -> Dict[str, str]:
        """
        Parse a diff to extract file changes.
        
        Args:
            diff: The code diff
            
        Returns:
            A dictionary mapping file paths to their contents
        """
        files = {}
        current_file = None
        current_content = []
        
        # Split the diff into lines
        lines = diff.split("\n")
        
        for line in lines:
            # Check if this is a new file header
            if line.startswith("--- a/") or line.startswith("+++ b/"):
                # Extract the file path
                if line.startswith("+++ b/"):
                    file_path = line[6:]
                    current_file = file_path
                    current_content = []
            elif current_file and line.startswith("+") and not line.startswith("+++"):
                # This is an added line, add it to the current file content
                current_content.append(line[1:])
            
            # If we've reached the end of a file, save its content
            if current_file and (line.startswith("diff ") or line == ""):
                if current_content:
                    files[current_file] = "\n".join(current_content)
                current_file = None
                current_content = []
        
        # Save the last file if there is one
        if current_file and current_content:
            files[current_file] = "\n".join(current_content)
        
        return files
    
    def _group_files_by_language(self, files: Dict[str, str]) -> Dict[str, Dict[str, str]]:
        """
        Group files by language.
        
        Args:
            files: A dictionary mapping file paths to their contents
            
        Returns:
            A dictionary mapping languages to dictionaries of file paths and contents
        """
        files_by_language = {}
        
        for file_path, content in files.items():
            # Get the file extension
            _, ext = os.path.splitext(file_path)
            
            # Determine the language
            language = self.supported_languages.get(ext)
            
            if language:
                if language not in files_by_language:
                    files_by_language[language] = {}
                
                files_by_language[language][file_path] = content
        
        return files_by_language
    
    def _run_python_linters(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run Python linters on the files.
        
        Args:
            files: A dictionary mapping file paths to their contents
            
        Returns:
            A dictionary containing linter results
        """
        results = {
            "language": "python",
            "issues": [],
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the files to the temporary directory
            for file_path, content in files.items():
                # Create the directory structure
                os.makedirs(os.path.dirname(os.path.join(temp_dir, file_path)), exist_ok=True)
                
                # Write the file
                with open(os.path.join(temp_dir, file_path), "w") as f:
                    f.write(content)
            
            # Run flake8
            for file_path in files.keys():
                try:
                    cmd = ["flake8", "--format=json", os.path.join(temp_dir, file_path)]
                    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                    
                    if output:
                        flake8_results = json.loads(output)
                        
                        for result in flake8_results:
                            results["issues"].append({
                                "file": file_path,
                                "line": result.get("line_number"),
                                "column": result.get("column_number"),
                                "message": result.get("text"),
                                "severity": "warning",
                                "source": "flake8",
                            })
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Error running flake8 on {file_path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing flake8 results for {file_path}: {str(e)}")
            
            # Run pylint
            for file_path in files.keys():
                try:
                    cmd = ["pylint", "--output-format=json", os.path.join(temp_dir, file_path)]
                    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                    
                    if output:
                        pylint_results = json.loads(output)
                        
                        for result in pylint_results:
                            severity = "info"
                            if result.get("type") in ["error", "fatal"]:
                                severity = "error"
                            elif result.get("type") in ["warning"]:
                                severity = "warning"
                            
                            results["issues"].append({
                                "file": file_path,
                                "line": result.get("line"),
                                "column": result.get("column"),
                                "message": result.get("message"),
                                "severity": severity,
                                "source": "pylint",
                            })
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Error running pylint on {file_path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing pylint results for {file_path}: {str(e)}")
        
        return results
    
    def _run_javascript_linters(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run JavaScript linters on the files.
        
        Args:
            files: A dictionary mapping file paths to their contents
            
        Returns:
            A dictionary containing linter results
        """
        results = {
            "language": "javascript",
            "issues": [],
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the files to the temporary directory
            for file_path, content in files.items():
                # Create the directory structure
                os.makedirs(os.path.dirname(os.path.join(temp_dir, file_path)), exist_ok=True)
                
                # Write the file
                with open(os.path.join(temp_dir, file_path), "w") as f:
                    f.write(content)
            
            # Create a basic ESLint configuration
            eslint_config = {
                "env": {
                    "browser": True,
                    "es2021": True,
                    "node": True
                },
                "extends": "eslint:recommended",
                "parserOptions": {
                    "ecmaVersion": 12,
                    "sourceType": "module"
                },
                "rules": {}
            }
            
            with open(os.path.join(temp_dir, ".eslintrc.json"), "w") as f:
                json.dump(eslint_config, f)
            
            # Run ESLint
            for file_path in files.keys():
                try:
                    cmd = ["eslint", "--format=json", os.path.join(temp_dir, file_path)]
                    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                    
                    if output:
                        eslint_results = json.loads(output)
                        
                        for result in eslint_results:
                            for message in result.get("messages", []):
                                severity = "info"
                                if message.get("severity") == 2:
                                    severity = "error"
                                elif message.get("severity") == 1:
                                    severity = "warning"
                                
                                results["issues"].append({
                                    "file": file_path,
                                    "line": message.get("line"),
                                    "column": message.get("column"),
                                    "message": message.get("message"),
                                    "severity": severity,
                                    "source": "eslint",
                                })
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Error running eslint on {file_path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing eslint results for {file_path}: {str(e)}")
        
        return results
    
    def _run_typescript_linters(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run TypeScript linters on the files.
        
        Args:
            files: A dictionary mapping file paths to their contents
            
        Returns:
            A dictionary containing linter results
        """
        results = {
            "language": "typescript",
            "issues": [],
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the files to the temporary directory
            for file_path, content in files.items():
                # Create the directory structure
                os.makedirs(os.path.dirname(os.path.join(temp_dir, file_path)), exist_ok=True)
                
                # Write the file
                with open(os.path.join(temp_dir, file_path), "w") as f:
                    f.write(content)
            
            # Create a basic TSConfig
            tsconfig = {
                "compilerOptions": {
                    "target": "es2020",
                    "module": "commonjs",
                    "strict": True,
                    "esModuleInterop": True,
                    "skipLibCheck": True,
                    "forceConsistentCasingInFileNames": True
                }
            }
            
            with open(os.path.join(temp_dir, "tsconfig.json"), "w") as f:
                json.dump(tsconfig, f)
            
            # Create a basic ESLint configuration for TypeScript
            eslint_config = {
                "env": {
                    "browser": True,
                    "es2021": True,
                    "node": True
                },
                "extends": [
                    "eslint:recommended",
                    "plugin:@typescript-eslint/recommended"
                ],
                "parser": "@typescript-eslint/parser",
                "parserOptions": {
                    "ecmaVersion": 12,
                    "sourceType": "module"
                },
                "plugins": [
                    "@typescript-eslint"
                ],
                "rules": {}
            }
            
            with open(os.path.join(temp_dir, ".eslintrc.json"), "w") as f:
                json.dump(eslint_config, f)
            
            # Run ESLint with TypeScript plugin
            for file_path in files.keys():
                try:
                    cmd = ["eslint", "--format=json", os.path.join(temp_dir, file_path)]
                    output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                    
                    if output:
                        eslint_results = json.loads(output)
                        
                        for result in eslint_results:
                            for message in result.get("messages", []):
                                severity = "info"
                                if message.get("severity") == 2:
                                    severity = "error"
                                elif message.get("severity") == 1:
                                    severity = "warning"
                                
                                results["issues"].append({
                                    "file": file_path,
                                    "line": message.get("line"),
                                    "column": message.get("column"),
                                    "message": message.get("message"),
                                    "severity": severity,
                                    "source": "eslint",
                                })
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Error running eslint on {file_path}: {str(e)}")
                except Exception as e:
                    logger.warning(f"Error processing eslint results for {file_path}: {str(e)}")
        
        return results
    
    def _run_java_linters(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run Java linters on the files.
        
        Args:
            files: A dictionary mapping file paths to their contents
            
        Returns:
            A dictionary containing linter results
        """
        # For Java, we would typically use tools like Checkstyle, PMD, or SpotBugs
        # This is a simplified implementation
        results = {
            "language": "java",
            "issues": [],
        }
        
        # Simple regex-based checks for common Java issues
        for file_path, content in files.items():
            # Check for empty catch blocks
            empty_catch_pattern = r"catch\s*\([^)]+\)\s*\{\s*\}"
            for match in re.finditer(empty_catch_pattern, content):
                line_number = content[:match.start()].count("\n") + 1
                results["issues"].append({
                    "file": file_path,
                    "line": line_number,
                    "column": 1,
                    "message": "Empty catch block",
                    "severity": "warning",
                    "source": "regex",
                })
            
            # Check for System.out.println
            println_pattern = r"System\.out\.println"
            for match in re.finditer(println_pattern, content):
                line_number = content[:match.start()].count("\n") + 1
                results["issues"].append({
                    "file": file_path,
                    "line": line_number,
                    "column": 1,
                    "message": "Use a logger instead of System.out.println",
                    "severity": "info",
                    "source": "regex",
                })
        
        return results
    
    def _run_csharp_linters(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run C# linters on the files.
        
        Args:
            files: A dictionary mapping file paths to their contents
            
        Returns:
            A dictionary containing linter results
        """
        # For C#, we would typically use tools like StyleCop or FxCop
        # This is a simplified implementation
        results = {
            "language": "csharp",
            "issues": [],
        }
        
        # Simple regex-based checks for common C# issues
        for file_path, content in files.items():
            # Check for empty catch blocks
            empty_catch_pattern = r"catch\s*\([^)]+\)\s*\{\s*\}"
            for match in re.finditer(empty_catch_pattern, content):
                line_number = content[:match.start()].count("\n") + 1
                results["issues"].append({
                    "file": file_path,
                    "line": line_number,
                    "column": 1,
                    "message": "Empty catch block",
                    "severity": "warning",
                    "source": "regex",
                })
            
            # Check for Console.WriteLine
            writeline_pattern = r"Console\.WriteLine"
            for match in re.finditer(writeline_pattern, content):
                line_number = content[:match.start()].count("\n") + 1
                results["issues"].append({
                    "file": file_path,
                    "line": line_number,
                    "column": 1,
                    "message": "Use a logger instead of Console.WriteLine",
                    "severity": "info",
                    "source": "regex",
                })
        
        return results
    
    def _run_go_linters(self, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Run Go linters on the files.
        
        Args:
            files: A dictionary mapping file paths to their contents
            
        Returns:
            A dictionary containing linter results
        """
        results = {
            "language": "go",
            "issues": [],
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the files to the temporary directory
            for file_path, content in files.items():
                # Create the directory structure
                os.makedirs(os.path.dirname(os.path.join(temp_dir, file_path)), exist_ok=True)
                
                # Write the file
                with open(os.path.join(temp_dir, file_path), "w") as f:
                    f.write(content)
            
            # Run go vet
            for file_path in files.keys():
                try:
                    cmd = ["go", "vet", os.path.join(temp_dir, file_path)]
                    subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
                except subprocess.CalledProcessError as e:
                    # go vet outputs errors to stdout
                    output = e.output
                    
                    # Parse the output
                    for line in output.split("\n"):
                        if ":" in line:
                            parts = line.split(":", 3)
                            if len(parts) >= 3:
                                try:
                                    line_number = int(parts[1])
                                    message = parts[2].strip()
                                    
                                    results["issues"].append({
                                        "file": file_path,
                                        "line": line_number,
                                        "column": 1,
                                        "message": message,
                                        "severity": "warning",
                                        "source": "go vet",
                                    })
                                except (ValueError, IndexError):
                                    pass
                except Exception as e:
                    logger.warning(f"Error running go vet on {file_path}: {str(e)}")
        
        return results