import json
from typing import List, Dict, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class JSONDatabase:
    def __init__(self, db_dir: str = "data"):
        self.db_dir = Path(db_dir)
        self.db_dir.mkdir(exist_ok=True)
        
        self.hackathons_file = self.db_dir / "hackathons.json"
        self.completed_hackathons_file = self.db_dir / "completed_hackathons.json"
        self.embeddings_file = self.db_dir / "embeddings.json"
        self.sessions_file = self.db_dir / "sessions.json"
        self.messages_file = self.db_dir / "messages.json"
        self.drafts_file = self.db_dir / "drafts.json"
        self.audit_log_file = self.db_dir / "audit_log.json"
        
        self._initialize_files()
    
    def _initialize_files(self):
        files_to_init = {
            self.hackathons_file: [],
            self.completed_hackathons_file: [],
            self.embeddings_file: [],
            self.sessions_file: {},
            self.messages_file: {},
            self.drafts_file: {},
            self.audit_log_file: []
        }
        
        for file_path, default_value in files_to_init.items():
            if not file_path.exists():
                self._write_json(file_path, default_value)
                logger.info(f"Initialized {file_path}")
    
    def _read_json(self, file_path: Path) -> Any:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {} if "sessions" in str(file_path) or "messages" in str(file_path) or "drafts" in str(file_path) else []
        except json.JSONDecodeError as e:
            logger.error(f"Error reading JSON from {file_path}: {e}")
            return {} if "sessions" in str(file_path) or "messages" in str(file_path) or "drafts" in str(file_path) else []
    
    def _write_json(self, file_path: Path, data: Any):
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            return True
        except Exception as e:
            logger.error(f"Error writing JSON to {file_path}: {e}")
            return False
    
    def save_hackathon(self, hackathon: Dict) -> bool:
        hackathons = self._read_json(self.hackathons_file)
        hackathons.append(hackathon)
        return self._write_json(self.hackathons_file, hackathons)
    
    def get_hackathons(self, status: Optional[str] = None) -> List[Dict]:
        hackathons = self._read_json(self.hackathons_file)
        if status:
            return [h for h in hackathons if h.get("status") == status]
        return hackathons
    
    def get_completed_hackathons(self, days_back: int = 7) -> List[Dict]:
        all_completed = self._read_json(self.completed_hackathons_file)
        hackathons = self.get_hackathons(status="completed")
        all_completed.extend(hackathons)
        
        if days_back:
            cutoff_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            cutoff_date = cutoff_date.replace(day=cutoff_date.day - days_back)
            
            filtered = []
            for h in all_completed:
                ended_at = h.get("ended_at") or h.get("created_at")
                if ended_at:
                    try:
                        if isinstance(ended_at, str):
                            ended_dt = datetime.fromisoformat(ended_at.replace('Z', '+00:00'))
                        else:
                            ended_dt = ended_at
                        if ended_dt >= cutoff_date:
                            filtered.append(h)
                    except:
                        pass
            
            return filtered
        
        return all_completed
    
    def mark_hackathon_completed(self, hackathon_id: str, hackathon_data: Dict) -> bool:
        completed = self._read_json(self.completed_hackathons_file)
        completed_hackathon = {
            **hackathon_data,
            "id": hackathon_id,
            "status": "completed",
            "ended_at": datetime.now().isoformat()
        }
        completed.append(completed_hackathon)
        return self._write_json(self.completed_hackathons_file, completed)
    
    def save_embedding(self, embedding: Dict) -> bool:
        embeddings = self._read_json(self.embeddings_file)
        embeddings.append(embedding)
        return self._write_json(self.embeddings_file, embeddings)
    
    def get_embeddings(self, status: Optional[str] = None) -> List[Dict]:
        embeddings = self._read_json(self.embeddings_file)
        if status:
            return [e for e in embeddings if e.get("metadata", {}).get("status") == status]
        return embeddings
    
    def update_embedding_status(self, embedding_id: str, status: str, admin_user_id: Optional[str] = None) -> bool:
        embeddings = self._read_json(self.embeddings_file)
        for emb in embeddings:
            if emb.get("id") == embedding_id:
                emb["metadata"]["status"] = status
                if admin_user_id:
                    emb["metadata"]["approved_by"] = admin_user_id
                    emb["metadata"]["approved_at"] = datetime.now().isoformat()
                return self._write_json(self.embeddings_file, embeddings)
        return False
    
    def get_pending_embeddings(self) -> List[Dict]:
        return self.get_embeddings(status="pending_approval")
    
    def get_approved_embeddings(self) -> List[Dict]:
        return self.get_embeddings(status="approved")
    
    def save_session(self, user_id: str, session_data: Dict) -> bool:
        sessions = self._read_json(self.sessions_file)
        sessions[user_id] = {
            **session_data,
            "updated_at": datetime.now().isoformat()
        }
        return self._write_json(self.sessions_file, sessions)
    
    def get_session(self, user_id: str) -> Optional[Dict]:
        sessions = self._read_json(self.sessions_file)
        return sessions.get(user_id)
    
    def update_session_step(self, user_id: str, step: int) -> bool:
        session = self.get_session(user_id) or {}
        session["current_step"] = step
        session["updated_at"] = datetime.now().isoformat()
        return self.save_session(user_id, session)
    
    def save_message(self, user_id: str, message: Dict) -> bool:
        messages = self._read_json(self.messages_file)
        if user_id not in messages:
            messages[user_id] = []
        messages[user_id].append({
            **message,
            "timestamp": datetime.now().isoformat()
        })
        return self._write_json(self.messages_file, messages)
    
    def get_messages(self, user_id: str) -> List[Dict]:
        messages = self._read_json(self.messages_file)
        return messages.get(user_id, [])
    
    def clear_messages(self, user_id: str) -> bool:
        messages = self._read_json(self.messages_file)
        if user_id in messages:
            del messages[user_id]
            return self._write_json(self.messages_file, messages)
        return True
    
    def save_draft(self, user_id: str, draft: Dict) -> bool:
        drafts = self._read_json(self.drafts_file)
        drafts[user_id] = {
            **draft,
            "updated_at": datetime.now().isoformat()
        }
        return self._write_json(self.drafts_file, drafts)
    
    def get_draft(self, user_id: str) -> Optional[Dict]:
        drafts = self._read_json(self.drafts_file)
        return drafts.get(user_id)
    
    def delete_draft(self, user_id: str) -> bool:
        drafts = self._read_json(self.drafts_file)
        if user_id in drafts:
            del drafts[user_id]
            return self._write_json(self.drafts_file, drafts)
        return True
    
    def log_audit_event(self, event_type: str, user_id: str, details: Dict) -> bool:
        audit_log = self._read_json(self.audit_log_file)
        audit_entry = {
            "id": f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}",
            "event_type": event_type,
            "user_id": user_id,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        audit_log.append(audit_entry)
        return self._write_json(self.audit_log_file, audit_log)
    
    def get_audit_log(self, user_id: Optional[str] = None, event_type: Optional[str] = None) -> List[Dict]:
        audit_log = self._read_json(self.audit_log_file)
        if user_id or event_type:
            filtered = []
            for entry in audit_log:
                if user_id and entry.get("user_id") != user_id:
                    continue
                if event_type and entry.get("event_type") != event_type:
                    continue
                filtered.append(entry)
            return filtered
        return audit_log


json_db = JSONDatabase()

