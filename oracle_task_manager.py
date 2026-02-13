#!/usr/bin/env python3
"""
ORACLE TASK MANAGER - Runs on Oracle VM
"""

import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
import uuid

class OracleTaskManager:
    """Manages AI tasks via GitHub bridge"""
    
    def __init__(self, repo_path="/home/ubuntu/ai-bridge-repo"):
        self.repo_path = Path(repo_path)
        self.tasks_dir = self.repo_path / 'tasks'
        self.results_dir = self.repo_path / 'results'
        
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Oracle Task Manager initialized")
        print(f"  Repo: {repo_path}")
    
    def _git_pull(self):
        try:
            subprocess.run(['git', 'pull'], cwd=self.repo_path, capture_output=True, timeout=30, check=True)
        except Exception as e:
            print(f"⚠️ Git pull failed: {e}")
    
    def _git_push(self, message="Oracle task"):
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, timeout=10, check=True)
            subprocess.run(['git', 'commit', '-m', message], cwd=self.repo_path, timeout=10, check=True)
            subprocess.run(['git', 'push'], cwd=self.repo_path, timeout=30, check=True)
            return True
        except Exception as e:
            print(f"⚠️ Git push failed: {e}")
            return False
    
    def ask_ai(self, ai_name, prompt, timeout=120):
        task_id = str(uuid.uuid4())[:8]
        
        print(f"\n{'='*60}")
        print(f"🤖 SENDING TASK TO AI")
        print(f"{'='*60}")
        print(f"Task ID: {task_id}")
        print(f"AI: {ai_name}")
        print(f"Prompt: {prompt[:100]}...")
        print(f"{'='*60}\n")
        
        task = {'id': task_id, 'ai': ai_name, 'prompt': prompt, 'timestamp': datetime.now().isoformat()}
        task_file = self.tasks_dir / f"task_{task_id}.json"
        
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        print(f"📤 Task created: {task_file.name}")
        
        if not self._git_push(f"Task {task_id}"):
            print("✗ Failed to push task")
            return None
        
        print("✓ Task pushed to GitHub")
        print("⏳ Waiting for AI response...")
        
        result_file = self.results_dir / f"result_{task_id}.json"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            self._git_pull()
            
            if result_file.exists():
                with open(result_file) as f:
                    result = json.load(f)
                
                response = result.get('response', '')
                print(f"\n✓ Response received ({len(response)} chars)")
                print(f"AI used: {result.get('ai_used')}")
                print(f"Time: {int(time.time() - start_time)}s")
                result_file.unlink()
                return response
            
            time.sleep(5)
        
        print(f"\n✗ Timeout waiting for response ({timeout}s)")
        return None

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 ORACLE TASK MANAGER                          ║
║            AI Bridge Communication Test                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    oracle = OracleTaskManager()
    response = oracle.ask_ai(ai_name="claude", prompt="Say 'AI Bridge is working!' and nothing else.")
    
    if response:
        print(f"\n{'='*60}")
        print("AI RESPONSE:")
        print(f"{'='*60}")
        print(response)
        print(f"{'='*60}\n")
        print("✅ AI BRIDGE TEST SUCCESSFUL!")
    else:
        print("\n❌ AI BRIDGE TEST FAILED")
