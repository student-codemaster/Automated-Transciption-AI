#  AI Audio Transcriber v2.0

Enhanced Podcast Analysis with Comprehensive Visualizations

---

##  What's New

-  7 Interactive Visualizations
-  Comprehensive Analytics Dashboard
-  Multi-Episode Testing Framework
-  Quality Assessment System
-  Hash-based Caching System** (100x faster repeats!)
-  Complete Documentation

---

##  Quick Start

bash
# Install dependencies
pip install -r requirements.txt

# Verify system setup
python check_system.py

# Launch the app (with automatic caching)
streamlit run streamlit_app_v2.py

# Test multiple episodes
python multi_episode_test.py data/

<<<<<<< HEAD
=======
# Data Set For the auto matic tanscription
Google Drive 
>>>>>>> bf91aff (clean upload)

---

## Caching System (NEW)

Instant results for repeated episodes using hash-based caching:

python
from pipeline import run_pipeline

# First run: Processes audio + caches results (~4min)
result = run_pipeline("data/episode.mp3", use_cache=True)

# Second run: Loads from cache (~0.05sec) 
result = run_pipeline("data/episode.mp3", use_cache=True)


Benefits:
- 100x-1000x faster for cached episodes
- Automatic cache invalidation (detects file changes)
- Efficient storage (~30-60MB per episode)
- Transparent integration (works with existing code)

