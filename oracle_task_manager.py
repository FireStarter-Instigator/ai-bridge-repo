#!/usr/bin/env python3
"""
ORACLE TASK MANAGER - Runs on Oracle VM
Sends tasks to your 24/7 PC via GitHub
Receives AI responses
Applies them directly to code WITHOUT reading (saves tokens!)

Usage:
    from oracle_task_manager import OracleTaskManager
    
    oracle = OracleTaskManager()
    response = oracle.ask_ai("claude", "Fix this error: ...")
    oracle.apply_response_to_file(response, "MyMethod.java")
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
        
        # Ensure directories exist
        self.tasks_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"✓ Oracle Task Manager initialized")
        print(f"  Repo: {repo_path}")
    
    def _git_pull(self):
        """Pull latest from GitHub"""
        try:
            subprocess.run(
                ['git', 'pull'],
                cwd=self.repo_path,
                capture_output=True,
                timeout=30,
                check=True
            )
        except Exception as e:
            print(f"⚠️ Git pull failed: {e}")
    
    def _git_push(self, message="Oracle task"):
        """Push task to GitHub"""
        try:
            subprocess.run(['git', 'add', '.'], cwd=self.repo_path, timeout=10, check=True)
            subprocess.run(['git', 'commit', '-m', message], cwd=self.repo_path, timeout=10, check=True)
            subprocess.run(['git', 'push'], cwd=self.repo_path, timeout=30, check=True)
            return True
        except Exception as e:
            print(f"⚠️ Git push failed: {e}")
            return False
    
    def ask_ai(self, ai_name, prompt, timeout=120):
        """
        Send prompt to AI and wait for response
        
        Args:
            ai_name: Which AI to use (claude, gemini, chatgpt, gml7)
            prompt: The prompt to send
            timeout: Max seconds to wait for response
        
        Returns:
            AI response text, or None if timeout
        """
        # Generate unique task ID
        task_id = str(uuid.uuid4())[:8]
        
        print(f"\n{'='*60}")
        print(f"🤖 SENDING TASK TO AI")
        print(f"{'='*60}")
        print(f"Task ID: {task_id}")
        print(f"AI: {ai_name}")
        print(f"Prompt: {prompt[:100]}...")
        print(f"{'='*60}\n")
        
        # Create task file
        task = {
            'id': task_id,
            'ai': ai_name,
            'prompt': prompt,
            'timestamp': datetime.now().isoformat()
        }
        
        task_file = self.tasks_dir / f"task_{task_id}.json"
        with open(task_file, 'w') as f:
            json.dump(task, f, indent=2)
        
        print(f"📤 Task created: {task_file.name}")
        
        # Push to GitHub
        if not self._git_push(f"Task {task_id}"):
            print("✗ Failed to push task")
            return None
        
        print("✓ Task pushed to GitHub")
        print("⏳ Waiting for AI response...")
        
        # Wait for result
        result_file = self.results_dir / f"result_{task_id}.json"
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Pull from GitHub
            self._git_pull()
            
            # Check if result exists
            if result_file.exists():
                # Read result
                with open(result_file) as f:
                    result = json.load(f)
                
                response = result.get('response', '')
                
                print(f"\n✓ Response received ({len(response)} chars)")
                print(f"AI used: {result.get('ai_used')}")
                print(f"Time: {int(time.time() - start_time)}s")
                
                # Clean up result file
                result_file.unlink()
                
                return response
            
            # Wait before checking again
            time.sleep(5)
        
        print(f"\n✗ Timeout waiting for response ({timeout}s)")
        return None
    
    def apply_response_to_file(self, response, filepath):
        """
        Apply AI response directly to file WITHOUT reading it
        (Saves tokens!)
        
        This assumes the response IS the complete file content
        
        Args:
            response: AI response (complete file content)
            filepath: Path to save to
        """
        print(f"\n📝 Applying response to: {filepath}")
        
        with open(filepath, 'w') as f:
            f.write(response)
        
        print(f"✓ File updated ({len(response)} chars)")
    
    def extract_code_from_response(self, response):
        """
        Extract code block from AI response
        Handles markdown code blocks
        
        Args:
            response: AI response with code
        
        Returns:
            Extracted code, or original response if no code block
        """
        # Look for markdown code blocks
        if '```java' in response:
            # Extract Java code block
            start = response.find('```java') + 7
            end = response.find('```', start)
            if end > start:
                return response[start:end].strip()
        
        elif '```' in response:
            # Extract generic code block
            start = response.find('```') + 3
            end = response.find('```', start)
            if end > start:
                return response[start:end].strip()
        
        # No code block found, return as-is
        return response.strip()

# =============================================================================
# EXAMPLE USAGE
# =============================================================================

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════╗
║                 ORACLE TASK MANAGER                          ║
║            AI Bridge Communication Test                      ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Initialize
    oracle = OracleTaskManager()
    
    # Test asking AI
    response = oracle.ask_ai(
        ai_name="claude",
        prompt="Say 'AI Bridge is working!' and nothing else."
    )
    
    if response:
        print(f"\n{'='*60}")
        print("AI RESPONSE:")
        print(f"{'='*60}")
        print(response)
        print(f"{'='*60}\n")
        
        print("✅ AI BRIDGE TEST SUCCESSFUL!")
    else:
        print("\n❌ AI BRIDGE TEST FAILED")
        print("\nTroubleshooting:")
        print("1. Is ai_bridge.py running on your 24/7 PC?")
        print("2. Are all browsers open and logged in?")
        print("3. Is GitHub repo syncing correctly?")
