# app/db.py
import pyodbc
from datetime import datetime
import json
from typing import List, Dict, Optional

class Database:
    def __init__(self):
        self.server = r"localhost\SQLEXPRESS"  # Change this
        self.database = "exam_monitoring_system"
        self.connection_string = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={self.server};"
            f"DATABASE={self.database};"
            f"Trusted_Connection=yes;"  # Windows auth
        )
    
    def get_connection(self):
        try:
            return pyodbc.connect(self.connection_string)
        except Exception as e:
            print(f"Database connection error: {e}")
            raise
    
    def insert_behavior_event(
        self,
        camera_id: int,
        behavior_label: str,
        confidence: float,
        severity: str,
        frame_timestamp: str,
        bbox: Optional[Dict] = None,
        recording_id: Optional[int] = None,
        frame_index: Optional[int] = None,
        extra_data: Optional[Dict] = None
    ) -> int:
        """Insert a behavior event and return its ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO behavior_events 
                (camera_id, recording_id, behavior_label, confidence, severity, 
                 frame_timestamp, frame_index, bbox, extra_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                camera_id,
                recording_id,
                behavior_label,
                confidence,
                severity,
                frame_timestamp,
                frame_index,
                json.dumps(bbox) if bbox else None,
                json.dumps(extra_data) if extra_data else None
            ))
            
            cursor.execute("SELECT @@IDENTITY AS id")
            behavior_id = cursor.fetchone()[0]
            
            conn.commit()
            return int(behavior_id)
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()
            conn.close()
    
    def get_recent_behaviors(self, camera_id: int, limit: int = 50) -> List[Dict]:
        """Get recent behavior events for a camera"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT TOP (?) 
                    id, camera_id, behavior_label, confidence, severity,
                    frame_timestamp, bbox, extra_data, created_at
                FROM behavior_events
                WHERE camera_id = ?
                ORDER BY frame_timestamp DESC
            """, (limit, camera_id))
            
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            
            results = []
            for row in rows:
                event = dict(zip(columns, row))
                # Parse JSON fields
                if event.get('bbox'):
                    event['bbox'] = json.loads(event['bbox'])
                if event.get('extra_data'):
                    event['extra_data'] = json.loads(event['extra_data'])
                # Convert datetime to string
                event['frame_timestamp'] = event['frame_timestamp'].isoformat()
                event['created_at'] = event['created_at'].isoformat()
                results.append(event)
            
            return results
        finally:
            cursor.close()
            conn.close()
    
    def get_cameras(self) -> List[Dict]:
        """Get all online cameras"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, camera_name, camera_ip, position, status
                FROM cameras
                WHERE status = 'online'
                ORDER BY camera_name
            """)
            
            rows = cursor.fetchall()
            columns = [column[0] for column in cursor.description]
            return [dict(zip(columns, row)) for row in rows]
        finally:
            cursor.close()
            conn.close()

db = Database()
