"""
Tests for the linter service.
"""
import pytest
from worker.linter_service import LinterService

def test_parse_diff():
    """Test parsing a diff."""
    # Create a linter service
    linter_service = LinterService()
    
    # Create a test diff
    diff = """diff --git a/test.py b/test.py
--- a/test.py
+++ b/test.py
@@ -1,3 +1,4 @@
 def hello():
-    print("Hello, world!")
+    # This is a comment
+    print("Hello, world!")
+    return None
diff --git a/test.js b/test.js
--- a/test.js
+++ b/test.js
@@ -1,3 +1,4 @@
 function hello() {
-    console.log("Hello, world!");
+    // This is a comment
+    console.log("Hello, world!");
+    return null;
"""
    
    # Parse the diff
    files = linter_service._parse_diff(diff)
    
    # Check the result
    assert len(files) == 2
    assert "test.py" in files
    assert "test.js" in files
    
    # Check the file contents
    assert files["test.py"] == 'def hello():\n    # This is a comment\n    print("Hello, world!")\n    return None'
    assert files["test.js"] == 'function hello() {\n    // This is a comment\n    console.log("Hello, world!");\n    return null;'

def test_group_files_by_language():
    """Test grouping files by language."""
    # Create a linter service
    linter_service = LinterService()
    
    # Create test files
    files = {
        "test.py": "def hello(): pass",
        "test.js": "function hello() {}",
        "test.ts": "function hello(): void {}",
        "test.java": "public class Test {}",
        "test.cs": "public class Test {}",
        "test.go": "package main",
        "test.txt": "Hello, world!",
    }
    
    # Group the files by language
    files_by_language = linter_service._group_files_by_language(files)
    
    # Check the result
    assert len(files_by_language) == 6
    assert "python" in files_by_language
    assert "javascript" in files_by_language
    assert "typescript" in files_by_language
    assert "java" in files_by_language
    assert "csharp" in files_by_language
    assert "go" in files_by_language
    
    # Check the file contents
    assert files_by_language["python"]["test.py"] == "def hello(): pass"
    assert files_by_language["javascript"]["test.js"] == "function hello() {}"
    assert files_by_language["typescript"]["test.ts"] == "function hello(): void {}"
    assert files_by_language["java"]["test.java"] == "public class Test {}"
    assert files_by_language["csharp"]["test.cs"] == "public class Test {}"
    assert files_by_language["go"]["test.go"] == "package main"