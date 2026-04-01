
from cache_manager import CacheManager
from pipeline import run_pipeline, get_cache_manager
import os


def example_basic_caching():
    """ Basic caching with default parameters."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Caching")
    print("="*60)
    
    audio_file = "data/episode1.mp3"
    
    # First run - processes the audio (slow)
    print("\n First run (no cache)...")
    result1 = run_pipeline(audio_file, use_cache=True)
    print(" Processing complete")
    
    # Second run - uses cache (fast!)
    print("\n Second run (with cache)...")
    result2 = run_pipeline(audio_file, use_cache=True)
    print(" Cached - instant results!")
    
    # Results are identical
    print(f"\nResults match: {result1 == result2}")


def example_cache_management():
    """Example 2: Cache management operations."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Cache Management")
    print("="*60)
    
    cache = get_cache_manager(".cache")
    
    # Get cache statistics
    print("\n Cache Statistics:")
    cache.print_cache_stats()
    
    # List all cached files
    print("\nCached Episodes:")
    for cache_key, metadata in cache.list_cached_files().items():
        print(f"  {cache_key}")
        print(f"    Created: {metadata['created']}")
        print(f"    Hash: {metadata['file_hash']}")


def example_cache_operations():
    """Example 3: Various cache operations."""
    print("\n" + "="*60)
    print(" Cache Operations")
    print("="*60)
    
    cache = get_cache_manager(".cache")
    audio_file = "data/episode1.mp3"
    
    # Check if cache exists
    if cache.cache_exists(audio_file):
        print(f" Cache exists for {audio_file}")
        
        # Get cache key
        cache_key = cache.get_cache_key(audio_file)
        print(f"Cache key: {cache_key}")
        
        # Get cache size
        size_mb = cache.get_cache_size(cache_key)
        print(f"Size: {size_mb:.2f} MB")
    else:
        print(f"No cache for {audio_file}")


def example_batch_processing_with_cache():
    """Example 4: Batch processing with cache."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Batch Processing with Cache")
    print("="*60)
    
    audio_files = [
        "data/episode1.mp3",
        "data/episode2.mp3",
        "data/episode3.mp3"
    ]
    
    print("\nProcessing multiple episodes...")
    for i, audio_file in enumerate(audio_files, 1):
        if os.path.exists(audio_file):
            print(f"\n{i}. Processing {audio_file}...")
            result = run_pipeline(audio_file, use_cache=True)
            print(f"Complete")
        else:
            print(f"\n{i}. {audio_file} not found (skipping)")
    
    # Show cache statistics
    cache = get_cache_manager(".cache")
    print("\n" + "-"*60)
    cache.print_cache_stats()


def example_force_reprocess():
    """Example 5: Force reprocessing (bypass cache)."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Force Reprocessing")
    print("="*60)
    
    audio_file = "data/episode1.mp3"
    
    # Bypass cache (use_cache=False)
    print(f"\nForcing reprocessing of {audio_file}...")
    result = run_pipeline(audio_file, use_cache=False)
    print("Reprocessing complete")


def example_cache_clearing():
    """Example 6: Clearing cache."""
    print("\n" + "="*60)
    print("EXAMPLE 6: Cache Clearing")
    print("="*60)
    
    cache = get_cache_manager(".cache")
    
    # Show current cache
    print("\nCurrent cache:")
    cache.print_cache_stats()
    
    # Clear specific cache (example)
    cache_list = cache.list_cached_files()
    if cache_list:
        first_key = list(cache_list.keys())[0]
        print(f"\nClearing cache for: {first_key}")
        cache.clear_cache(first_key)
    
    # Show updated cache
    print("\nCache after clearing:")
    cache.print_cache_stats()


def example_hash_calculation():
    """Example 7: Understanding file hashing."""
    print("\n" + "="*60)
    print("EXAMPLE 7: File Hashing")
    print("="*60)
    
    cache = get_cache_manager(".cache")
    audio_file = "data/episode1.mp3"
    
    if os.path.exists(audio_file):
        # Get file hash
        file_hash = cache.get_file_hash(audio_file)
        print(f"\nFile: {audio_file}")
        print(f"SHA256 Hash: {file_hash}")
        
        # Get cache key (hash + filename)
        cache_key = cache.get_cache_key(audio_file)
        print(f"Cache Key:  {cache_key}")
        
        print("\n How it works:")
        print("- Same audio file = same hash")
        print("- Modified audio file = different hash")
        print("- Hash + filename = unique cache key")
        print("- Cache bypassed if file content changes")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("CACHE SYSTEM EXAMPLES")
    print("="*60)
    
    # Uncomment examples to run:
    
    # example_basic_caching()
    # example_cache_management()
    # example_cache_operations()
    # example_batch_processing_with_cache()
    # example_force_reprocess()
    # example_cache_clearing()
    # example_hash_calculation()
    
    print("\nUncomment examples in code to run them")
    print("\nQuick start:")
    print("from cache_manager import CacheManager")
    print("cache = CacheManager()")
    print("cache.print_cache_stats()  # View cache")
    print("\nOr use pipeline with caching:")
    print("from pipeline import run_pipeline")
    print("result = run_pipeline('data/episode.mp3', use_cache=True)")
