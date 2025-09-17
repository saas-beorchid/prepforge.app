#!/usr/bin/env python3
"""
JSON FILE REPAIR TOOL
====================

Fixes corrupted JSON files in questions_data/ directory
"""

import json
import os
import re

def fix_json_file(file_path):
    """Fix common JSON formatting issues"""
    print(f"🔧 Fixing {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # Remove any trailing commas before closing brackets/braces
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Handle multiple JSON objects by wrapping in array
        if content.count('}{') > 0:
            # Split on }{ and wrap each in array
            parts = content.split('}{')
            if len(parts) > 1:
                # Add missing braces
                parts[0] += '}'
                for i in range(1, len(parts)-1):
                    parts[i] = '{' + parts[i] + '}'
                parts[-1] = '{' + parts[-1]
                
                # Wrap in array
                content = '[' + ','.join(parts) + ']'
        
        # Try to parse and reformat
        try:
            data = json.loads(content)
            
            # Save fixed version
            backup_path = file_path + '.backup'
            os.rename(file_path, backup_path)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Fixed {file_path} - {len(data) if isinstance(data, list) else 1} questions")
            return True
            
        except json.JSONDecodeError as e:
            print(f"❌ Still invalid JSON after fix attempt: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False

def main():
    """Fix all corrupted JSON files"""
    json_files = [
        'GMAT_Questions.json',
        'GRE_Questions.json', 
        'MCAT_Questions.json',
        'USMLE_STEP_1_Questions.json',
        'USMLE_STEP_2_Questions.json',
        'NCLEX_Questions.json',
        'LSAT_Questions.json',
        'IELTS_Questions.json',
        'TOEFL_Questions(Reading).json',
        'PMP_Questions.json',
        'CFA_Questions.json',
        'ACT_Questions.json',
        'SAT_Questions.json'
    ]
    
    json_path = './questions_data'
    fixed_count = 0
    
    print("🚀 STARTING JSON FILE REPAIR")
    print("=" * 50)
    
    for filename in json_files:
        file_path = os.path.join(json_path, filename)
        
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    json.loads(content)  # Test if valid
                print(f"✅ {filename} - Already valid")
            except json.JSONDecodeError:
                if fix_json_file(file_path):
                    fixed_count += 1
        else:
            print(f"⚠️ {filename} - File not found")
    
    print("=" * 50)
    print(f"🎯 REPAIR COMPLETE: {fixed_count} files fixed")

if __name__ == "__main__":
    main()