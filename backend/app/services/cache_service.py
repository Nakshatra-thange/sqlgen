import time
import json
import hashlib
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import logging
from threading import Lock

logger = logging.getLogger(__name__)


class CacheEntry:
    """Represents a single cache entry with metadata"""
    
    def __init__(self, key: str, value: Any, ttl_seconds: int = 1800):
        self.key = key
        self.value = value
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.ttl_seconds = ttl_seconds
        self.access_count = 0
    
    def is_expired(self) -> bool:
        """Check if the cache entry has expired"""
        return time.time() - self.created_at > self.ttl_seconds
    
    def is_stale(self, stale_threshold_seconds: int = 300) -> bool:
        """Check if the cache entry is stale (not recently accessed)"""
        return time.time() - self.last_accessed > stale_threshold_seconds
    
    def access(self):
        """Mark the entry as accessed"""
        self.last_accessed = time.time()
        self.access_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert cache entry to dictionary for serialization"""
        return {
            "key": self.key,
            "value": self.value,
            "created_at": self.created_at,
            "last_accessed": self.last_accessed,
            "ttl_seconds": self.ttl_seconds,
            "access_count": self.access_count
        }


class CacheService:
    """Service for caching database schema, relationships, and other data"""
    
    def __init__(self, max_size: int = 100, cleanup_interval: int = 300):
        self._cache: Dict[str, CacheEntry] = {}
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()
        self._lock = Lock()
        
        # Cache prefixes for different types of data
        self.PREFIXES = {
            "schema": "schema:",
            "relationships": "rel:",
            "tables": "table:",
            "statistics": "stats:",
            "join_paths": "path:",
            "analysis": "analysis:"
        }
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments"""
        key_parts = [prefix] + [str(arg) for arg in args]
        key_string = ":".join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _cleanup_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return
        
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired()
            ]
            
            for key in expired_keys:
                del self._cache[key]
                logger.debug(f"Removed expired cache entry: {key}")
            
            self._last_cleanup = current_time
    
    def _evict_if_needed(self):
        """Evict least recently used entries if cache is full"""
        if len(self._cache) < self._max_size:
            return
        
        with self._lock:
            # Sort by last accessed time and remove oldest
            sorted_entries = sorted(
                self._cache.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove 20% of oldest entries
            evict_count = max(1, len(sorted_entries) // 5)
            for i in range(evict_count):
                key, _ = sorted_entries[i]
                del self._cache[key]
                logger.debug(f"Evicted cache entry: {key}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache"""
        self._cleanup_expired()
        
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            
            if entry.is_expired():
                del self._cache[key]
                return None
            
            entry.access()
            return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: int = 1800) -> bool:
        """Set a value in cache with TTL"""
        self._cleanup_expired()
        self._evict_if_needed()
        
        with self._lock:
            entry = CacheEntry(key, value, ttl_seconds)
            self._cache[key] = entry
            logger.debug(f"Cached entry: {key} (TTL: {ttl_seconds}s)")
            return True
    
    def delete(self, key: str) -> bool:
        """Delete a cache entry"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Deleted cache entry: {key}")
                return True
            return False
    
    def clear(self, prefix: Optional[str] = None) -> int:
        """Clear cache entries, optionally by prefix"""
        with self._lock:
            if prefix is None:
                count = len(self._cache)
                self._cache.clear()
                logger.info(f"Cleared all cache entries ({count} entries)")
                return count
            
            keys_to_delete = [
                key for key in self._cache.keys()
                if key.startswith(prefix)
            ]
            
            for key in keys_to_delete:
                del self._cache[key]
            
            logger.info(f"Cleared cache entries with prefix '{prefix}' ({len(keys_to_delete)} entries)")
            return len(keys_to_delete)
    
    def exists(self, key: str) -> bool:
        """Check if a key exists in cache and is not expired"""
        self._cleanup_expired()
        
        with self._lock:
            entry = self._cache.get(key)
            if entry is None or entry.is_expired():
                return False
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            current_time = time.time()
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired())
            active_entries = total_entries - expired_entries
            
            # Calculate average access count
            total_access = sum(entry.access_count for entry in self._cache.values())
            avg_access = total_access / total_entries if total_entries > 0 else 0
            
            # Calculate memory usage (rough estimate)
            memory_usage = sum(
                len(str(entry.value)) for entry in self._cache.values()
            )
            
            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "max_size": self._max_size,
                "utilization_percent": (total_entries / self._max_size) * 100 if self._max_size > 0 else 0,
                "total_access_count": total_access,
                "average_access_count": avg_access,
                "estimated_memory_bytes": memory_usage,
                "last_cleanup": datetime.fromtimestamp(self._last_cleanup).isoformat()
            }
    
    # Schema-specific cache methods
    def get_schema(self, database_name: str) -> Optional[Dict[str, Any]]:
        """Get cached database schema"""
        key = self._generate_key(self.PREFIXES["schema"], database_name)
        return self.get(key)
    
    def set_schema(self, database_name: str, schema: Dict[str, Any], ttl_seconds: int = 1800) -> bool:
        """Cache database schema"""
        key = self._generate_key(self.PREFIXES["schema"], database_name)
        return self.set(key, schema, ttl_seconds)
    
    def clear_schema_cache(self, database_name: Optional[str] = None) -> int:
        """Clear schema cache"""
        if database_name:
            key = self._generate_key(self.PREFIXES["schema"], database_name)
            return 1 if self.delete(key) else 0
        else:
            return self.clear(self.PREFIXES["schema"])
    
    # Table-specific cache methods
    def get_table_info(self, database_name: str, table_name: str) -> Optional[Dict[str, Any]]:
        """Get cached table information"""
        key = self._generate_key(self.PREFIXES["tables"], database_name, table_name)
        return self.get(key)
    
    def set_table_info(self, database_name: str, table_name: str, table_info: Dict[str, Any], ttl_seconds: int = 3600) -> bool:
        """Cache table information"""
        key = self._generate_key(self.PREFIXES["tables"], database_name, table_name)
        return self.set(key, table_info, ttl_seconds)
    
    # Relationship-specific cache methods
    def get_relationships(self, database_name: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached relationships"""
        key = self._generate_key(self.PREFIXES["relationships"], database_name)
        return self.get(key)
    
    def set_relationships(self, database_name: str, relationships: List[Dict[str, Any]], ttl_seconds: int = 1800) -> bool:
        """Cache relationships"""
        key = self._generate_key(self.PREFIXES["relationships"], database_name)
        return self.set(key, relationships, ttl_seconds)
    
    # Join path cache methods
    def get_join_paths(self, database_name: str, start_table: str, end_table: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached join paths"""
        key = self._generate_key(self.PREFIXES["join_paths"], database_name, start_table, end_table)
        return self.get(key)
    
    def set_join_paths(self, database_name: str, start_table: str, end_table: str, paths: List[Dict[str, Any]], ttl_seconds: int = 3600) -> bool:
        """Cache join paths"""
        key = self._generate_key(self.PREFIXES["join_paths"], database_name, start_table, end_table)
        return self.set(key, paths, ttl_seconds)
    
    # Statistics cache methods
    def get_statistics(self, database_name: str, table_name: str) -> Optional[Dict[str, Any]]:
        """Get cached table statistics"""
        key = self._generate_key(self.PREFIXES["statistics"], database_name, table_name)
        return self.get(key)
    
    def set_statistics(self, database_name: str, table_name: str, statistics: Dict[str, Any], ttl_seconds: int = 7200) -> bool:
        """Cache table statistics"""
        key = self._generate_key(self.PREFIXES["statistics"], database_name, table_name)
        return self.set(key, statistics, ttl_seconds)


# Global cache service instance
cache_service = CacheService() 