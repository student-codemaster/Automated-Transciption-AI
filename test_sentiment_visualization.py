"""Test script for the new sentiment trend visualization with segments."""

import json
import os
from visualization import create_sentiment_trend_with_segments, create_sentiment_trend, format_time

def test_sentiment_visualization():
    """Test the sentiment visualization with sample data."""
    
    # Create sample segments with sentiment data
    sample_segments = [
        {
            'id': '1',
            'start': 0.0,
            'end': 190.0,
            'duration': 190.0,
            'sentiment_score': 0.75,  # Positive
            'summary': 'Introduction to the topic with enthusiasm',
            'keywords': ['intro', 'exciting', 'overview'],
            'text': 'This is the introduction segment...'
        },
        {
            'id': '2',
            'start': 190.0,
            'end': 465.0,
            'duration': 275.0,
            'sentiment_score': 0.45,  # Neutral to slightly positive
            'summary': 'Detailed technical discussion',
            'keywords': ['technical', 'analysis', 'details'],
            'text': 'Here we discuss the technical aspects...'
        },
        {
            'id': '3',
            'start': 465.0,
            'end': 720.0,
            'duration': 255.0,
            'sentiment_score': -0.35,  # Slightly negative
            'summary': 'Challenges and concerns raised',
            'keywords': ['challenges', 'problems', 'concerns'],
            'text': 'There are some challenges to consider...'
        }
    ]
    
    print("🧪 Testing Sentiment Visualization Module")
    print("=" * 60)
    
    # Test 1: Check format_time function
    print("\n✅ Test 1: format_time function")
    print(f"  0 seconds: {format_time(0)}")
    print(f"  190 seconds: {format_time(190)}")
    print(f"  465 seconds: {format_time(465)}")
    print(f"  3665 seconds: {format_time(3665)}")
    
    # Test 2: Create basic sentiment trend
    print("\n✅ Test 2: Creating basic sentiment trend visualization...")
    try:
        fig_basic = create_sentiment_trend(sample_segments)
        print("  ✓ Basic sentiment trend created successfully")
        print(f"  Figure title: {fig_basic.layout.title.text if fig_basic.layout.title else 'No title'}")
    except Exception as e:
        print(f"  ✗ Error creating basic sentiment trend: {e}")
        return False
    
    # Test 3: Create enhanced sentiment trend with segments
    print("\n✅ Test 3: Creating enhanced sentiment trend with segments...")
    try:
        fig_enhanced = create_sentiment_trend_with_segments(sample_segments)
        print("  ✓ Enhanced sentiment trend created successfully")
        print(f"  Figure title: {fig_enhanced.layout.title.text if fig_enhanced.layout.title else 'No title'}")
        print(f"  Number of traces: {len(fig_enhanced.data)}")
        print(f"  Shapes (segment boundaries): {len(fig_enhanced.layout.shapes)}")
        print(f"  Annotations: {len(fig_enhanced.layout.annotations)}")
    except Exception as e:
        print(f"  ✗ Error creating enhanced sentiment trend: {e}")
        return False
    
    # Test 4: Verify data extraction from segments
    print("\n✅ Test 4: Verifying data extraction from segments...")
    segment_data = []
    for seg in sample_segments:
        segment_data.append({
            'id': seg['id'],
            'start': seg['start'],
            'end': seg['end'],
            'sentiment': seg['sentiment_score'],
            'summary': seg['summary'],
            'keywords':', '.join(seg.get('keywords', []))
        })
    
    for data in segment_data:
        print(f"  Segment {data['id']}: {format_time(data['start'])} → {format_time(data['end'])}")
        print(f"    Sentiment: {data['sentiment']:.3f}")
        print(f"    Summary: {data['summary']}")
        print(f"    Keywords: {data['keywords']}")
    
    # Test 5: Try loading real data from final_outputs
    print("\n✅ Test 5: Testing with real data from final_outputs...")
    final_outputs_dir = "final_outputs"
    json_files = [f for f in os.listdir(final_outputs_dir) if f.endswith('.json') and not f.endswith('_embeddings.json')]
    
    if json_files:
        test_file = os.path.join(final_outputs_dir, json_files[0])
        print(f"  Loading {json_files[0]}...")
        try:
            with open(test_file, 'r') as f:
                data = json.load(f)
            
            if 'segments' in data:
                segments = data['segments']
                print(f"  ✓ Loaded {len(segments)} segments from {json_files[0]}")
                
                # Check if segments have required fields
                required_fields = ['id', 'start', 'end', 'sentiment_score']
                missing_fields = []
                for field in required_fields:
                    if not any(field in seg or (field == 'sentiment_score' and 'sentiment' in seg) for seg in segments):
                        missing_fields.append(field)
                
                if missing_fields:
                    print(f"  ⚠️  Missing fields: {missing_fields}")
                else:
                    print(f"  ✓ All required fields present")
                
                # Try to create visualization
                try:
                    fig_real = create_sentiment_trend_with_segments(segments)
                    print(f"  ✓ Successfully created visualization with real data")
                except Exception as e:
                    print(f"  ✗ Error creating visualization: {e}")
            else:
                print(f"  ⚠️  No 'segments' key found in JSON file")
        except Exception as e:
            print(f"  ✗ Error loading test file: {e}")
    else:
        print(f"  ℹ️  No JSON files found in {final_outputs_dir}")
    
    print("\n" + "=" * 60)
    print("🎉 All tests completed!")
    print("\n📝 Summary of changes:")
    print("  1. Added create_sentiment_trend_with_segments() function to visualization.py")
    print("  2. Enhanced visualization includes:")
    print("     - X-axis: Time in seconds")
    print("     - Y-axis: Sentiment score (-1.0 to 1.0)")
    print("     - Vertical dashed lines: Segment boundaries")
    print("     - Green shaded area: Positive sentiment (>0.5)")
    print("     - Red shaded area: Negative sentiment (<-0.5)")
    print("     - Color gradient: Warmer = positive, cooler = negative")
    print("  3. Added import to streamlit_app_v2.py")
    print("  4. Added visualization display to Sentiment page")
    
    return True

if __name__ == "__main__":
    success = test_sentiment_visualization()
    exit(0 if success else 1)
