#!/usr/bin/env python3
"""
Code Issues Validation Script
Addresses common issues found in the code review
"""

import os
import re
import json
from pathlib import Path

class CodeValidator:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.issues_found = []
        self.issues_fixed = []
    
    def log_issue(self, file_path, line_num, issue, severity="Medium"):
        self.issues_found.append({
            "file": str(file_path),
            "line": line_num,
            "issue": issue,
            "severity": severity
        })
    
    def log_fix(self, file_path, fix_description):
        self.issues_fixed.append({
            "file": str(file_path),
            "fix": fix_description
        })
    
    def check_environment_variables(self):
        """Check for hardcoded secrets and environment variable issues"""
        env_file = self.project_root / ".env"
        if env_file.exists():
            with open(env_file, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for exposed API keys
                    if "OPENAI_API_KEY=sk-" in line and not line.startswith("#"):
                        self.log_issue(env_file, i, "Exposed OpenAI API key in .env file", "Critical")
                    
                    # Check for weak JWT secrets
                    if "JWT_SECRET=" in line and "change-in-production" in line:
                        self.log_issue(env_file, i, "Default JWT secret should be changed", "High")
    
    def check_sql_injection_risks(self):
        """Check for potential SQL injection vulnerabilities"""
        backend_files = list(self.project_root.glob("backend/**/*.py"))
        
        for file_path in backend_files:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for string formatting in SQL queries
                    if re.search(r'\.format\(.*\)|%.*%|f".*{.*}"', line) and any(sql_word in line.lower() for sql_word in ['select', 'insert', 'update', 'delete']):
                        self.log_issue(file_path, i, "Potential SQL injection risk - use parameterized queries", "High")
    
    def check_error_handling(self):
        """Check for proper error handling"""
        python_files = list(self.project_root.glob("**/*.py"))
        
        for file_path in python_files:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                in_try_block = False
                has_specific_except = False
                
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    
                    if stripped.startswith('try:'):
                        in_try_block = True
                        has_specific_except = False
                    
                    elif stripped.startswith('except:') and in_try_block:
                        self.log_issue(file_path, i, "Bare except clause - specify exception types", "Medium")
                        has_specific_except = True
                    
                    elif stripped.startswith('except ') and in_try_block:
                        has_specific_except = True
                    
                    elif stripped.startswith(('def ', 'class ', 'if ', 'for ', 'while ')) and in_try_block:
                        in_try_block = False
    
    def check_input_validation(self):
        """Check for input validation issues"""
        backend_files = list(self.project_root.glob("backend/**/*.py"))
        
        for file_path in backend_files:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for direct user input usage
                    if re.search(r'request\.(json|form|args|values)', line) and 'validate' not in line.lower():
                        self.log_issue(file_path, i, "User input should be validated", "Medium")
    
    def check_frontend_security(self):
        """Check frontend security issues"""
        frontend_files = list(self.project_root.glob("frontend/**/*.tsx")) + list(self.project_root.glob("frontend/**/*.ts"))
        
        for file_path in frontend_files:
            with open(file_path, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
                for i, line in enumerate(lines, 1):
                    # Check for localStorage usage without encryption
                    if 'localStorage.setItem' in line and 'token' in line:
                        self.log_issue(file_path, i, "Consider encrypting sensitive data in localStorage", "Low")
                    
                    # Check for dangerouslySetInnerHTML
                    if 'dangerouslySetInnerHTML' in line:
                        self.log_issue(file_path, i, "Potential XSS risk with dangerouslySetInnerHTML", "High")
    
    def apply_automatic_fixes(self):
        """Apply automatic fixes for common issues"""
        
        # Fix .env.example to not expose real API key
        env_example = self.project_root / ".env.example"
        if env_example.exists():
            with open(env_example, 'r') as f:
                content = f.read()
            
            if "sk-proj-" in content:
                content = re.sub(r'OPENAI_API_KEY=sk-[^\n]+', 'OPENAI_API_KEY=your-openai-api-key-here', content)
                content = re.sub(r'JWT_SECRET=your-super-secret-jwt-key-change-in-production', 'JWT_SECRET=your-super-secret-jwt-key-change-in-production-minimum-32-chars', content)
                
                with open(env_example, 'w') as f:
                    f.write(content)
                
                self.log_fix(env_example, "Removed exposed API key and improved JWT secret template")
    
    def generate_report(self):
        """Generate a comprehensive report"""
        print("🔍 Code Validation Report")
        print("=" * 50)
        
        if not self.issues_found:
            print("✅ No critical issues found!")
        else:
            print(f"Found {len(self.issues_found)} issues:")
            
            # Group by severity
            critical = [i for i in self.issues_found if i['severity'] == 'Critical']
            high = [i for i in self.issues_found if i['severity'] == 'High']
            medium = [i for i in self.issues_found if i['severity'] == 'Medium']
            low = [i for i in self.issues_found if i['severity'] == 'Low']
            
            for severity, issues in [('Critical', critical), ('High', high), ('Medium', medium), ('Low', low)]:
                if issues:
                    print(f"\n🔴 {severity} Issues ({len(issues)}):")
                    for issue in issues:
                        print(f"  • {issue['file']}:{issue['line']} - {issue['issue']}")
        
        if self.issues_fixed:
            print(f"\n✅ Applied {len(self.issues_fixed)} automatic fixes:")
            for fix in self.issues_fixed:
                print(f"  • {fix['file']} - {fix['fix']}")
        
        print("\n📋 Recommendations:")
        print("1. Review the Code Issues Panel for detailed findings")
        print("2. Run the system tests: ./run_tests.sh")
        print("3. Open frontend_test.html to monitor network calls")
        print("4. Test authentication flow manually")
        print("5. Verify WebSocket connections work properly")
    
    def run_all_checks(self):
        """Run all validation checks"""
        print("🔍 Running code validation checks...")
        
        self.check_environment_variables()
        self.check_sql_injection_risks()
        self.check_error_handling()
        self.check_input_validation()
        self.check_frontend_security()
        self.apply_automatic_fixes()
        
        self.generate_report()

def main():
    project_root = os.getcwd()
    validator = CodeValidator(project_root)
    validator.run_all_checks()

if __name__ == "__main__":
    main()