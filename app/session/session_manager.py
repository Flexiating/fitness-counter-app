import json
from pathlib import Path
class SessionManager:
 def __init__(self,path=None): self.path=Path(path or 'data/sessions.json')
 def save(self,data):
  self.path.parent.mkdir(parents=True,exist_ok=True); rows=json.loads(self.path.read_text()) if self.path.exists() else []; rows.append(data); self.path.write_text(json.dumps(rows,indent=2))
