"""
Cache Manager for Audio Processing Pipeline
"""

import hashlib
import json
import os
import pickle
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional, Any


class CacheManager:
    """Manages caching of pipeline results using file hashing."""
    def __init__(self, cache_dir: str = ".cache"):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / "cache_metadata.json"
        self.load_metadata()
    
    def load_metadata(self):
        """Load cache metadata from disk."""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"Failed to load cache metadata: {e}")
                self.metadata = {}
        else:
            self.metadata = {}
    
    def save_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"Failed to save cache metadata: {e}")
    
    @staticmethod
    def get_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
        """Calculate hash of a file.
        
        Args:
            file_path: Path to file to hash
            algorithm: Hash algorithm ('sha256', 'md5')
        
        Returns:
            Hex digest of file hash
        """
        hasher = hashlib.new(algorithm)
        
        try:
            with open(file_path, 'rb') as f:
                # Read in chunks for memory efficiency
                for chunk in iter(lambda: f.read(4096), b''):
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            print(f"Error calculating file hash: {e}")
            return None
    
    def get_cache_key(self, file_path: str) -> str:
        """Get cache key for a file (based on hash + filename).
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Cache key string
        """
        file_hash = self.get_file_hash(file_path)
        if file_hash is None:
            return None
        
        filename = Path(file_path).stem  # filename without extension
        return f"{filename}_{file_hash[:12]}"  # shorter hash for readability
    
    def get_cache_path(self, cache_key: str, data_type: str = 'results') -> Path:
        """Get full path for cached data.
        
        Args:
            cache_key: Cache key
            data_type: Type of data ('results', 'embeddings', 'metadata')
        
        Returns:
            Path to cache file
        """
        return self.cache_dir / f"{cache_key}_{data_type}.pkl"
    
    def get_metadata_path(self, cache_key: str) -> Path:
        """Get path for cache metadata file."""
        return self.cache_dir / f"{cache_key}_meta.json"
    
    def cache_exists(self, file_path: str) -> bool:
        """Check if cache exists for a file.
        
        Args:
            file_path: Path to audio file
        
        Returns:
            True if cache exists
        """
        cache_key = self.get_cache_key(file_path)
        if cache_key is None:
            return False
        
        results_path = self.get_cache_path(cache_key, 'results')
        meta_path = self.get_metadata_path(cache_key)
        
        return results_path.exists() and meta_path.exists()
    
    def load_cache(self, file_path: str) -> Optional[Tuple]:
        """Load cached pipeline results.
        
        Args:
            file_path: Path to audio file
        
        Returns:
            Tuple of (transcript, topics, sentiment_score, summaries, index, search_engine)
            or None if cache doesn't exist
        """
        if not self.cache_exists(file_path):
            return None
        
        cache_key = self.get_cache_key(file_path)
        results_path = self.get_cache_path(cache_key, 'results')
        
        try:
            with open(results_path, 'rb') as f:
                data = pickle.load(f)
            print(f"Loaded from cache: {cache_key}")
            return data
        except Exception as e:
            print(f"Failed to load cache: {e}")
            return None
    
    def save_cache(self, file_path: str, results: Tuple, 
                   embeddings_data: Optional[Dict] = None) -> bool:
        """Save pipeline results to cache.
        
        Args:
            file_path: Path to audio file
            results: Tuple of pipeline results
            embeddings_data: Optional embeddings data
        
        Returns:
            True if successful
        """
        cache_key = self.get_cache_key(file_path)
        if cache_key is None:
            return False
        
        # Save results
        results_path = self.get_cache_path(cache_key, 'results')
        try:
            with open(results_path, 'wb') as f:
                pickle.dump(results, f)
            print(f"Results cached: {cache_key}")
        except Exception as e:
            print(f"Failed to cache results: {e}")
            return False
        
        # Save embeddings if provided
        if embeddings_data:
            embeddings_path = self.get_cache_path(cache_key, 'embeddings')
            try:
                with open(embeddings_path, 'wb') as f:
                    pickle.dump(embeddings_data, f)
                print(f"Embeddings cached: {cache_key}")
            except Exception as e:
                print(f"Failed to cache embeddings: {e}")
        
        # Save metadata
        meta_path = self.get_metadata_path(cache_key)
        metadata = {
            "cache_key": cache_key,
            "file_path": file_path,
            "file_hash": self.get_file_hash(file_path)[:12],
            "created": datetime.now().isoformat(),
            "has_embeddings": embeddings_data is not None
        }
        
        try:
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
        except Exception as e:
            print(f"Failed to save cache metadata: {e}")
        
        # Update global metadata
        self.metadata[cache_key] = metadata
        self.save_metadata()
        
        return True
    
    def clear_cache(self, cache_key: Optional[str] = None) -> bool:
        """Clear cache for specific key or all caches.
        
        Args:
            cache_key: Specific cache key to clear, or None to clear all
        
        Returns:
            True if successful
        """
        try:
            if cache_key:
                # Clear specific cache
                for data_type in ['results', 'embeddings', 'meta']:
                    if data_type == 'meta':
                        path = self.get_metadata_path(cache_key)
                    else:
                        path = self.get_cache_path(cache_key, data_type)
                    
                    if path.exists():
                        path.unlink()
                
                if cache_key in self.metadata:
                    del self.metadata[cache_key]
                
                print(f"Cleared cache: {cache_key}")
            else:
                # Clear all caches
                for path in self.cache_dir.glob("*"):
                    if path != self.metadata_file:
                        path.unlink()
                self.metadata = {}
                print(f"Cleared all caches")
            
            self.save_metadata()
            return True
        except Exception as e:
            print(f"Failed to clear cache: {e}")
            return False
    
    def get_cache_size(self, cache_key: Optional[str] = None) -> float:
        """Get cache size in MB.
        Args:
            cache_key: Specific cache key, or None for total
        Returns:
            Size in MB
        """
        total_bytes = 0
        
        if cache_key:
            for data_type in ['results', 'embeddings']:
                path = self.get_cache_path(cache_key, data_type)
                if path.exists():
                    total_bytes += path.stat().st_size
        else:
            for path in self.cache_dir.glob("*.pkl"):
                total_bytes += path.stat().st_size
        
        return total_bytes / (1024 * 1024)  # Convert to MB
    
    def list_cached_files(self) -> Dict[str, Dict]:
        """List all cached files with metadata.
        Returns:
            Dictionary of cache_key -> metadata
        """
        return self.metadata.copy()
    
    def print_cache_stats(self):
        """Print cache statistics."""
        print("\n" + "=" * 60)
        print("CACHE STATISTICS")
        print("=" * 60)
        
        cache_list = self.list_cached_files()
        if not cache_list:
            print("Cache is empty")
            return
        
        print(f"Total cached files: {len(cache_list)}")
        total_size = self.get_cache_size()
        print(f"Total cache size:   {total_size:.2f} MB")
        print()
        
        print("Cached Episodes:")
        for cache_key, meta in cache_list.items():
            size = self.get_cache_size(cache_key)
            has_embed = "YES" if meta.get('has_embeddings') else "NO"
            print(f"  {cache_key:50s} {size:6.2f} MB (embeddings: {has_embed})")
        
        print("=" * 60 + "\n")


def create_cache_manager(cache_dir: str = ".cache") -> CacheManager:
    """Factory function to create cache manager.
    Args:
        cache_dir: Cache directory
    Returns:
        CacheManager instance
    """
    return CacheManager(cache_dir)
