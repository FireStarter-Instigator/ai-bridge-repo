#!/usr/bin/env python3
"""
MICROBOT AUTONOMOUS WATCHER - Linux/Oracle VM Version

Monitors microbot.jar execution, detects failures, communicates with AI Bridge

Requirements:
- Oracle VM with microbot repo at ~/microbot/
- AI Bridge repo at ~/ai-bridge-repo/
- Tor Browser running (SOCKS5 on 127.0.0.1:9150)
- Screenshots saved by microbot plugin to ~/microbot-screenshots/

Architecture:
1. Runner: Launches microbot.jar with Tor proxy
2. Watcher: Monitors for crashes, connection loss, stuck states
3. Architect: Sends issues to AI Bridge (Jules/Claude/Gemini)
4. Builder: Pulls fixes, rebuilds, restarts

DO NOT MODIFY pom.xml versions!
"""

import os
import sys
import time
import subprocess
import json
import psutil
from pathlib import Path
from datetime import datetime
import signal

# =============================================================================
# CONFIGURATION
# =============================================================================

# Paths
MICROBOT_DIR = Path("/home/ubuntu/ai-bridge-repo")
MICROBOT_JAR = MICROBOT_DIR / "main_WildyKiller_aesthetic.jar"
AI_BRIDGE_REPO = Path("/home/ubuntu/ai-bridge-repo")
SCREENSHOT_DIR = Path("/home/ubuntu/microbot-screenshots")
LOG_DIR = Path("/home/ubuntu/watcher-logs")

# Tor proxy settings
TOR_PROXY_HOST = "127.0.0.1"
TOR_PROXY_PORT = "9150"

# Monitoring settings
CHECK_INTERVAL = 30  # seconds
RESTART_DELAY = 10  # seconds after crash
MAX_RESTART_ATTEMPTS = 3

# Create directories
SCREENSHOT_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

# =============================================================================
# MICROBOT RUNNER
# =============================================================================

class MicrobotRunner:
    """Manages microbot.jar process"""
    
    def __init__(self):
        self.process = None
        self.start_time = None
        self.restart_count = 0
    
    def start(self):
        """Launch microbot.jar with Tor proxy"""
        
        # Check Tor is running
        if not self._check_tor():
            print("⚠️ Tor proxy not available!")
            return False
        
        # Java command with Tor proxy
        cmd = [
            "java",
            f"-DsocksProxyHost={TOR_PROXY_HOST}",
            f"-DsocksProxyPort={TOR_PROXY_PORT}",
            "-Djava.net.preferIPv4Stack=true",
            "-jar",
            str(MICROBOT_JAR)
        ]
        
        print(f"\n{'='*60}")
        print(f"🚀 LAUNCHING MICROBOT")
        print(f"{'='*60}")
        print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Command: {' '.join(cmd)}")
        print(f"Proxy: {TOR_PROXY_HOST}:{TOR_PROXY_PORT}")
        print(f"{'='*60}\n")
        
        try:
            # Launch process
            self.process = subprocess.Popen(
                cmd,
                cwd=MICROBOT_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            self.start_time = time.time()
            print(f"✓ Microbot started (PID: {self.process.pid})")
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to start microbot: {e}")
            return False
    
    def _check_tor(self):
        """Check if Tor proxy is available"""
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((TOR_PROXY_HOST, int(TOR_PROXY_PORT)))
            sock.close()
            return result == 0
        except:
            return False
    
    def is_running(self):
        """Check if process is still running"""
        if self.process is None:
            return False
        return self.process.poll() is None
    
    def get_uptime(self):
        """Get process uptime in seconds"""
        if self.start_time:
            return int(time.time() - self.start_time)
        return 0
    
    def stop(self):
        """Gracefully stop the process"""
        if self.process and self.is_running():
            print("🛑 Stopping microbot...")
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("⚠️ Force killing...")
                self.process.kill()
            print("✓ Microbot stopped")

# =============================================================================
# ISSUE DETECTOR
# =============================================================================

class IssueDetector:
    """Detects crashes, connection loss, stuck states"""
    
    def __init__(self):
        self.last_screenshot = None
        self.last_screenshot_time = 0
    
    def check_for_issues(self, runner):
        """
        Check for various issues
        
        Returns:
            dict with issue info, or None if all good
        """
        # Check if process crashed
        if not runner.is_running():
            return {
                'type': 'CRASH',
                'description': 'Microbot process terminated unexpectedly',
                'uptime': runner.get_uptime()
            }
        
        # Check for connection loss (look for recent screenshots)
        issue = self._check_screenshots()
        if issue:
            return issue
        
        # All good
        return None
    
    def _check_screenshots(self):
        """Check recent screenshots for issues"""
        
        # Get most recent screenshot
        screenshots = sorted(SCREENSHOT_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime)
        
        if not screenshots:
            # No screenshots yet, probably just started
            return None
        
        latest = screenshots[-1]
        
        # If screenshot is same as last check, might be stuck
        if latest == self.last_screenshot:
            time_stuck = time.time() - self.last_screenshot_time
            if time_stuck > 300:  # 5 minutes same screenshot = stuck
                return {
                    'type': 'STUCK',
                    'description': 'Bot appears stuck (same screenshot for 5+ minutes)',
                    'screenshot': str(latest)
                }
        else:
            self.last_screenshot = latest
            self.last_screenshot_time = time.time()
        
        # Could add more checks here:
        # - OCR for "Connection Lost" message
        # - Compare screenshots for movement
        # - Check log file for errors
        
        return None

# =============================================================================
# AI BRIDGE INTEGRATION
# =============================================================================

class AIBridgeClient:
    """Communicates with AI Bridge for issue resolution"""
    
    def __init__(self):
        # Import oracle task manager
        sys.path.insert(0, str(AI_BRIDGE_REPO))
        from oracle_task_manager import OracleTaskManager
        
        self.oracle = OracleTaskManager(str(AI_BRIDGE_REPO))
    
    def request_fix(self, issue):
        """
        Send issue to AI and get fix
        
        Args:
            issue: Dict with type, description, screenshot (optional)
        
        Returns:
            Fix instructions or code
        """
        print(f"\n{'='*60}")
        print(f"🤖 REQUESTING AI ANALYSIS")
        print(f"{'='*60}")
        print(f"Issue: {issue['type']}")
        print(f"Description: {issue['description']}")
        print(f"{'='*60}\n")
        
        # Build prompt
        prompt = f"""
MICROBOT ISSUE DETECTED

Type: {issue['type']}
Description: {issue['description']}
"""
        
        if 'screenshot' in issue:
            prompt += f"\nScreenshot: {issue['screenshot']}"
            prompt += "\n(Screenshot available in microbot-screenshots/ directory)"
        
        if 'uptime' in issue:
            prompt += f"\nUptime before crash: {issue['uptime']} seconds"
        
        prompt += """

Please analyze this issue and provide:
1. Likely cause
2. How to fix it
3. Any code changes needed

If code changes are needed, provide complete Java file(s).
"""
        
        # Send to AI (route to appropriate AI)
        # For vision tasks (stuck detection), use Claude
        # For code fixes, use Gemini or Jules
        
        if issue['type'] == 'STUCK' and 'screenshot' in issue:
            ai = 'claude'  # Needs vision
        else:
            ai = 'gemini_1'  # Code fixes
        
        response = self.oracle.ask_ai(ai, prompt, timeout=120)
        
        if response:
            print(f"✓ AI response received ({len(response)} chars)")
        else:
            print(f"✗ No response from AI")
        
        return response

# =============================================================================
# BUILDER
# =============================================================================

class MicrobotBuilder:
    """Handles git pull, Maven rebuild"""
    
    def __init__(self):
        self.microbot_dir = MICROBOT_DIR
    
    def pull_latest(self):
        """Pull latest code from GitHub"""
        print("\n📥 Pulling latest code from GitHub...")
        
        try:
            result = subprocess.run(
                ['git', 'pull'],
                cwd=self.microbot_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✓ Git pull successful")
                if 'Already up to date' in result.stdout:
                    return False  # No changes
                return True  # Changes pulled
            else:
                print(f"⚠️ Git pull failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Git pull error: {e}")
            return False
    
    def rebuild(self):
        """Rebuild with Maven"""
        print("\n🔨 Building with Maven...")
        
        try:
            result = subprocess.run(
                ['mvn', 'clean', 'install', '-DskipTests'],
                cwd=self.microbot_dir,
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            if result.returncode == 0:
                print("✓ Build successful!")
                return True
            else:
                print(f"✗ Build failed!")
                print(result.stderr[-500:])  # Last 500 chars of error
                return False
                
        except Exception as e:
            print(f"✗ Build error: {e}")
            return False

# =============================================================================
# MAIN AUTONOMOUS LOOP
# =============================================================================

class AutonomousWatcher:
    """Main orchestrator"""
    
    def __init__(self):
        self.runner = MicrobotRunner()
        self.detector = IssueDetector()
        self.ai_bridge = AIBridgeClient()
        self.builder = MicrobotBuilder()
        
        self.running = True
        self.restart_count = 0
    
    def handle_shutdown(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        print("\n\n👋 Shutdown requested...")
        self.running = False
        self.runner.stop()
        sys.exit(0)
    
    def run(self):
        """Main autonomous loop"""
        
        # Setup signal handler
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)
        
        print("""
╔══════════════════════════════════════════════════════════════╗
║           MICROBOT AUTONOMOUS WATCHER v1.0                   ║
║         Recursive AI Factory - Linux Edition                 ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Initial start
        if not self.runner.start():
            print("❌ Failed to start microbot. Exiting.")
            return
        
        print(f"\n🔍 Monitoring microbot (Check interval: {CHECK_INTERVAL}s)...")
        
        while self.running:
            try:
                time.sleep(CHECK_INTERVAL)
                
                # Check for issues
                issue = self.detector.check_for_issues(self.runner)
                
                if issue:
                    print(f"\n⚠️ ISSUE DETECTED: {issue['type']}")
                    print(f"Description: {issue['description']}")
                    
                    # Stop current process
                    self.runner.stop()
                    
                    # Check if we should auto-restart or get AI help
                    if issue['type'] == 'CRASH' and self.restart_count < MAX_RESTART_ATTEMPTS:
                        # Simple crash, try restart
                        print(f"\n♻️ Auto-restart ({self.restart_count + 1}/{MAX_RESTART_ATTEMPTS})")
                        self.restart_count += 1
                        time.sleep(RESTART_DELAY)
                        self.runner.start()
                        continue
                    
                    # Complex issue or too many crashes - get AI help
                    print("\n🤖 Requesting AI assistance...")
                    
                    fix = self.ai_bridge.request_fix(issue)
                    
                    if fix:
                        # AI provided fix
                        # For now, assume code was committed to GitHub
                        # Pull and rebuild
                        
                        if self.builder.pull_latest():
                            print("📥 New code pulled from GitHub")
                            
                            if self.builder.rebuild():
                                print("✅ Build successful - restarting with fix...")
                                self.restart_count = 0  # Reset counter
                                time.sleep(RESTART_DELAY)
                                self.runner.start()
                            else:
                                print("❌ Build failed - waiting for manual intervention")
                                break
                        else:
                            print("⚠️ No new code to pull - AI might not have committed yet")
                            print("Restarting anyway...")
                            time.sleep(RESTART_DELAY)
                            self.runner.start()
                    else:
                        print("❌ No fix received from AI")
                        break
                
                else:
                    # All good, show status
                    uptime = self.runner.get_uptime()
                    print(f"✓ Running OK (Uptime: {uptime}s, PID: {self.runner.process.pid})", end='\r')
                
            except Exception as e:
                print(f"\n⚠️ Error in main loop: {e}")
                time.sleep(CHECK_INTERVAL)
        
        print("\n\n👋 Autonomous watcher stopped")

# =============================================================================
# ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    watcher = AutonomousWatcher()
    watcher.run()
