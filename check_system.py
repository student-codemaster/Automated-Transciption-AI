
import os
import sys
import json
import importlib
from datetime import datetime

# Fix Unicode encoding on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

class SimpleValidator:
    """Quick validation of system without complex imports."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
    
    def check(self, name, condition, details=""):
        """Print simple check result."""
        if condition:
            print(f"  [OK] {name}")
            self.passed += 1
        else:
            print(f"  [FAIL] {name} - {details}")
            self.failed += 1
        return condition
    
    def run(self):
        print("\n" + "="*70)
        print("SYSTEM VALIDATION - Quick Check")
        print("="*70)
        
        # Check files
        print("\n1. FILES & DIRECTORIES:")
        files = {
            'streamlit_app_v2.py': 'Frontend',
            'pipeline.py': 'Backend Pipeline',
            'visualization.py': 'Visualization',
            'audio_preprocess.py': 'Audio Processing',
            'speech_to_text.py': 'Speech Recognition',
            'keywords.py': 'Keywords',
            'sentiment.py': 'Sentiment',
            'summarizer.py': 'Summarizer',
            'segment_indexing.py': 'Indexing',
            'search.py': 'Search',
            'multi_episode_test.py': 'Testing',
        }
        
        for fname, desc in files.items():
            self.check(f"{fname} ({desc})", os.path.exists(fname))
        
        dirs = ['data', 'final_outputs', 'test_results']
        for dirname in dirs:
            exists = os.path.isdir(dirname)
            if not exists:
                os.makedirs(dirname, exist_ok=True)
                exists = True
            self.check(f"Directory: {dirname}", exists)
        
        # Check imports (backend only, skip Streamlit)
        print("\n2. BACKEND IMPORTS:")
        backend_modules = [
            'pipeline',
            'audio_preprocess',
            'speech_to_text',
            'keywords',
            'sentiment',
            'summarizer',
            'segment_indexing',
            'search',
            'visualization',
            'multi_episode_test',
        ]
        
        for mod in backend_modules:
            try:
                importlib.import_module(mod)
                self.check(f"Import {mod}", True)
            except Exception as e:
                self.check(f"Import {mod}", False, str(e)[:40])
        
        # Check dependencies
        print("\n3. KEY DEPENDENCIES:")
        deps = [
            'librosa',
            'numpy',
            'pandas',
            'torch',
            'transformers',
            'plotly',
            'wordcloud',
            'streamlit',
        ]
        
        for dep in deps:
            try:
                mod = importlib.import_module(dep.replace('-', '_'))
                ver = getattr(mod, '__version__', '?')
                self.check(f"{dep} ({ver})", True)
            except:
                self.check(f"{dep}", False, "Not installed")
        
        # Check pipeline signature
        print("\n4. PIPELINE INTEGRATION:")
        try:
            from pipeline import run_pipeline
            import inspect
            sig = inspect.signature(run_pipeline)
            params = list(sig.parameters.keys())
            self.check(f"run_pipeline function", True, f"params: {params}")
        except Exception as e:
            self.check(f"run_pipeline", False, str(e)[:40])
        
        # Check visualization functions
        print("\n5. VISUALIZATION FUNCTIONS:")
        try:
            from visualization import (
                create_segment_timeline,
                create_sentiment_trend_with_segments,
                create_keyword_cloud,
                create_keyword_bar_chart,
                create_keywords_per_segment,
            )
            self.check("Visualization functions", True)
        except Exception as e:
            self.check("Visualization functions", False, str(e)[:40])
        
        # Check sample data
        print("\n6. SAMPLE DATA:")
        sample_files = [
            'final_outputs/audio1.json',
            'data/health_speech_audio.mp3',
        ]
        for f in sample_files:
            exists = os.path.exists(f)
            status = "OK" if exists else "Optional"
            print(f"  [{status}] {f}")
        
        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        total = self.passed + self.failed
        pct = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n  Checks Passed: {self.passed}/{total} ({pct:.0f}%)")
        
        if self.failed == 0:
            print("\n  >>> SYSTEM READY! <<<")
            print("\n  Next steps:")
            print("  1. Start frontend: streamlit run streamlit_app_v2.py")
            print("  2. Run tests: python multi_episode_test.py data/")
            print("  3. Upload audio files to 'data/' folder")
            return True
        else:
            print(f"\n  [!] {self.failed} checks failed")
            print("  Fix issues and re-run validation")
            return False

if __name__ == "__main__":
    validator = SimpleValidator()
    success = validator.run()
    
    # Save to file for reference
    with open('validation_results.txt', 'w') as f:
        f.write(f"Validation Status: {'PASS' if success else 'FAIL'}\n")
        f.write(f"Timestamp: {datetime.now().isoformat()}\n")
    
    sys.exit(0 if success else 1)
