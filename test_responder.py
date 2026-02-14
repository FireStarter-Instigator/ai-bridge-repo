import json
import time
from pathlib import Path

print("Simple responder running...")

while True:
    # Check for tasks
    for task_file in Path('tasks').glob('task_*.json'):
        print(f"Found task: {task_file.name}")
        
        # Read task
        with open(task_file) as f:
            task = json.load(f)
        
        # Create simple response
        result = {
            'task_id': task['id'],
            'response': f"WINDOWS PC RECEIVED: {task['prompt']}",
            'status': 'success'
        }
        
        # Save result
        result_file = Path('results') / f"result_{task['id']}.json"
        with open(result_file, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"Created response: {result_file.name}")
        
        # Delete task
        task_file.unlink()
    
    time.sleep(5)