
import sqlite3
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AudioDatabase:
    """Manages SQLite database for audio processing results."""
    
    def __init__(self, db_path: str = "audio_database.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Create database and tables if they don't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create main results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_records (
                    serial_number INTEGER PRIMARY KEY AUTOINCREMENT,
                    audio_filename TEXT NOT NULL UNIQUE,
                    audio_path TEXT NOT NULL,
                    file_hash TEXT,
                    transcript TEXT,
                    summary TEXT,
                    sentiment_score REAL,
                    num_segments INTEGER,
                    keywords TEXT,
                    processing_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_time_seconds REAL,
                    file_size_mb REAL,
                    status TEXT DEFAULT 'COMPLETED'
                )
            ''')
            
            # Create index for faster queries
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_filename 
                ON audio_records(audio_filename)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_date 
                ON audio_records(processing_date)
            ''')
            
            conn.commit()
            conn.close()
            print(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            print(f"Database initialization error: {e}")
    
    def save_record(self, 
                   audio_filename: str,
                   audio_path: str,
                   transcript: str,
                   summary: str,
                   sentiment_score: float,
                   file_hash: Optional[str] = None,
                   num_segments: int = 0,
                   keywords: Optional[str] = None,
                   processing_time: float = 0.0,
                   file_size_mb: float = 0.0) -> bool:
     
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Truncate transcript and summary for display
            transcript_preview = transcript[:500] if transcript else ""
            summary_preview = summary[:500] if summary else ""
            
            cursor.execute('''
                INSERT INTO audio_records (
                    audio_filename, audio_path, file_hash, transcript, 
                    summary, sentiment_score, num_segments, keywords,
                    processing_time_seconds, file_size_mb
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                audio_filename,
                audio_path,
                file_hash,
                transcript_preview,
                summary_preview,
                float(sentiment_score),
                num_segments,
                keywords,
                float(processing_time),
                float(file_size_mb)
            ))
            
            conn.commit()
            serial_number = cursor.lastrowid
            conn.close()
            
            print(f"Record saved: #{serial_number} - {audio_filename}")
            return True
            
        except sqlite3.IntegrityError:
            print(f"Record already exists: {audio_filename}")
            return False
        except Exception as e:
            print(f"Error saving record: {e}")
            return False
    
    def get_all_records(self) -> List[Dict]:
        """Get all records from database.
        
        Returns:
            List of record dictionaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM audio_records 
                ORDER BY serial_number DESC
            ''')
            
            records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return records
            
        except Exception as e:
            print(f"Error retrieving records: {e}")
            return []
    
    def get_record_by_serial(self, serial_number: int) -> Optional[Dict]:
        """Get specific record by serial number.
        
        Args:
            serial_number: Serial number of record
        
        Returns:
            Record dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM audio_records 
                WHERE serial_number = ?
            ''', (serial_number,))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
            
        except Exception as e:
            print(f"Error retrieving record: {e}")
            return None
    
    def get_record_by_filename(self, filename: str) -> Optional[Dict]:
        """Get record by audio filename.
        Args:
            filename: Audio filename
        Returns:
            Record dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT * FROM audio_records 
                WHERE audio_filename = ?
            ''', (filename,))
            
            row = cursor.fetchone()
            conn.close()
            
            return dict(row) if row else None
            
        except Exception as e:
            print(f"Error retrieving record: {e}")
            return None
    
    def search_records(self, query: str) -> List[Dict]:
        """Search records by filename or keywords.
        Args:
            query: Search term
        Returns:
            List of matching records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            search_term = f"%{query}%"
            cursor.execute('''
                SELECT * FROM audio_records 
                WHERE audio_filename LIKE ? 
                   OR keywords LIKE ?
                   OR transcript LIKE ?
                ORDER BY serial_number DESC
            ''', (search_term, search_term, search_term))
            
            records = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return records
            
        except Exception as e:
            print(f"Error searching records: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """Get database statistics.
        
        Returns:
            Dictionary with stats
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total records
            cursor.execute('SELECT COUNT(*) FROM audio_records')
            total_records = cursor.fetchone()[0]
            
            # Average sentiment
            cursor.execute('SELECT AVG(sentiment_score) FROM audio_records')
            avg_sentiment = cursor.fetchone()[0] or 0
            
            # Average processing time
            cursor.execute('SELECT AVG(processing_time_seconds) FROM audio_records')
            avg_processing_time = cursor.fetchone()[0] or 0
            
            # Total file size
            cursor.execute('SELECT SUM(file_size_mb) FROM audio_records')
            total_file_size = cursor.fetchone()[0] or 0
            
            conn.close()
            
            stats = {
                'total_records': total_records,
                'avg_sentiment_score': round(avg_sentiment, 3),
                'avg_processing_time_sec': round(avg_processing_time, 2),
                'total_storage_mb': round(total_file_size, 2)
            }
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def delete_record(self, serial_number: int) -> bool:
        """Delete a record from database.
        Args:
            serial_number: Serial number of record to delete
        Returns:
            True if successful
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM audio_records WHERE serial_number = ?', 
                          (serial_number,))
            
            conn.commit()
            conn.close()
            
            print(f"Record deleted: #{serial_number}")
            return True
            
        except Exception as e:
            print(f"Error deleting record: {e}")
            return False
    
    def export_to_csv(self, output_path: str = "audio_records.csv") -> bool:
        """Export all records to CSV file.
        Args:
            output_path: Path to output CSV file       
        Returns:
            True if successful
        """
        try:
            import csv
            records = self.get_all_records()
            
            if not records:
                print("No records to export")
                return False
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=records[0].keys())
                writer.writeheader()
                writer.writerows(records)
            
            print(f"Exported to CSV: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False
    
    def export_to_json(self, output_path: str = "audio_records.json") -> bool:
        """Export all records to JSON file.
        Args:
            output_path: Path to output JSON file
        Returns:
            True if successful
        """
        try:
            records = self.get_all_records()
            
            if not records:
                print("No records to export")
                return False
            
            # Convert datetime fields to strings
            for record in records:
                if 'processing_date' in record:
                    record['processing_date'] = str(record['processing_date'])
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2, ensure_ascii=False)
            
            print(f"Exported to JSON: {output_path}")
            return True
            
        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False
    
    def print_database(self, limit: int = 10):
        """Print database contents in table format.
        Args:
            limit: Number of records to display
        """
        try:
            records = self.get_all_records()[:limit]
            if not records:
                print("Database is empty")
                return
            
            print("\n" + "="*120)
            print(f"{'#':>4} | {'Audio File':30} | {'Transcript (Preview)':35} | {'Sentiment':>10} | {'Date':19}")
            print("="*120)
            
            for record in records:
                serial = record['serial_number']
                filename = record['audio_filename'][:28]
                transcript = (record['transcript'][:33] + "...") if record['transcript'] else "N/A"
                sentiment = f"{record['sentiment_score']:.3f}" if record['sentiment_score'] is not None else "N/A"
                date = str(record['processing_date'])[:19]
                
                print(f"{serial:>4} | {filename:30} | {transcript:35} | {sentiment:>10} | {date:19}")
            
            print("="*120 + "\n")
            
        except Exception as e:
            print(f" Error printing database: {e}")
    
    def get_table_data_for_display(self, limit: int = 100) -> List[Dict]:
        """Get data formatted for Streamlit table display.
        
        Args:
            limit: Max records to return
        
        Returns:
            List of simplified records for UI display
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    serial_number,
                    audio_filename,
                    transcript,
                    summary,
                    sentiment_score,
                    num_segments,
                    processing_date
                FROM audio_records 
                ORDER BY serial_number DESC
                LIMIT ?
            ''', (limit,))
            
            columns = ['Serial #', 'Audio File', 'Transcript', 'Summary', 'Sentiment', 'Segments', 'Date']
            rows = cursor.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    'Serial #': row[0],
                    'Audio File': row[1][:40],
                    'Transcript': (row[2][:50] + "...") if row[2] else "N/A",
                    'Summary': (row[3][:50] + "...") if row[3] else "N/A",
                    'Sentiment': f"{row[4]:.3f}" if row[4] is not None else "N/A",
                    'Segments': row[5],
                    'Date': str(row[6])[:19]
                })
            
            return data
            
        except Exception as e:
            print(f"Error getting display data: {e}")
            return []


def create_database(db_path: str = "audio_database.db") -> AudioDatabase:
    """Factory function to create and return database instance.
    
    Args:
        db_path: Path to database file
    
    Returns:
        AudioDatabase instance
    """
    return AudioDatabase(db_path)
