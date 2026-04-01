"""Enhanced Streamlit app with comprehensive visualizations."""

import streamlit as st
import os
import shutil
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import numpy as np
import json

# Configure network timeouts and caching
os.environ['TRANSFORMERS_OFFLINE'] = '0'  # Allow online model loading
os.environ['HF_HUB_OFFLINE'] = '0'

# Use lazy imports to handle network timeouts gracefully
try:
    from pipeline import run_pipeline
    from visualization import (
        create_segment_timeline,
        create_sentiment_trend,
        create_keyword_cloud,
        create_keyword_bar_chart
    )
    from database import AudioDatabase
    IMPORTS_SUCCESSFUL = True
except Exception as e:
    IMPORTS_SUCCESSFUL = False
    IMPORT_ERROR = str(e)

# Page config
st.set_page_config(
    page_title="AI Audio Transcriber", 
    layout="wide",
    page_icon="🎙️",
    initial_sidebar_state="expanded"
)

st.title(" AI Audio Transcriber & Analyzer")
st.markdown("---")

# Check if imports were successful
if not IMPORTS_SUCCESSFUL:
    st.error(" Failed to initialize application")
    st.error(f"Error: {IMPORT_ERROR}")
    st.info("""
    This usually means:
    1. Network timeout downloading ML models
    2. Missing dependencies
    
    **Solutions:**
    1. Check your internet connection
    2. Restart the app: `streamlit run streamlit_app_v2.py`
    3. Reinstall dependencies: `pip install -r requirements.txt`
    """)
    st.stop()

# Initialize session state
if "analysis_complete" not in st.session_state:
    st.session_state.analysis_complete = False
    st.session_state.index = None
    st.session_state.search_engine = None
    st.session_state.topics = None
    st.session_state.transcript = None
    st.session_state.sentiment_score = None
    st.session_state.database = AudioDatabase("audio_database.db")

# Sidebar
with st.sidebar:
    st.header(" Configuration")
    st.markdown("Upload your podcast audio file and let AI analyze it!")
    
    uploaded_file = st.file_uploader(" Upload Podcast Audio", type=["wav", "mp3"], 
                                   help="Supported formats: WAV, MP3")
    
    # Playable audio player
    if uploaded_file:
        st.divider()
        st.subheader(" Audio Player")
        st.audio(uploaded_file)
    elif st.session_state.get("audio_path") and os.path.exists(st.session_state.audio_path):
        st.divider()
        st.subheader(" Audio Player")
        with open(st.session_state.audio_path, "rb") as af:
            st.audio(af.read(), format="audio/wav" if st.session_state.audio_path.endswith(".wav") else "audio/mpeg")
    
    if uploaded_file and st.button(" Analyze Podcast", use_container_width=True, type="primary"):
        with st.spinner("Processing audio... This may take a few minutes"):
            # Save uploaded file temporarily then copy to data folder
            local_path = uploaded_file.name
            with open(local_path, "wb") as f:
                f.write(uploaded_file.read())

            data_dir = "data"
            os.makedirs(data_dir, exist_ok=True)
            stored_path = os.path.join(data_dir, os.path.basename(local_path))
            # ensure unique name if file already exists
            counter = 1
            base, ext = os.path.splitext(stored_path)
            while os.path.exists(stored_path):
                stored_path = f"{base}_{counter}{ext}"
                counter += 1
            shutil.copy(local_path, stored_path)

            try:
                # Run pipeline on stored audio
                transcript, topics, sentiment_score, summaries, index, search_engine = run_pipeline(stored_path)
                
                # Store in session state
                st.session_state.transcript = transcript
                st.session_state.topics = topics
                st.session_state.sentiment_score = sentiment_score
                st.session_state.index = index
                st.session_state.search_engine = search_engine
                st.session_state.analysis_complete = True
                st.session_state.audio_path = stored_path
                
                # Save to database
                try:
                    audio_filename = os.path.basename(stored_path)
                    file_size_mb = os.path.getsize(stored_path) / (1024 * 1024)
                    
                    # Combine all summaries
                    combined_summary = " ".join(summaries) if summaries else ""
                    
                    # Combine all keywords
                    all_keywords = []
                    for topic in topics:
                        all_keywords.extend(topic.get('keywords', []))
                    keywords_str = ", ".join(set(all_keywords))
                    
                    st.session_state.database.save_record(
                        audio_filename=audio_filename,
                        audio_path=stored_path,
                        transcript=transcript,
                        summary=combined_summary,
                        sentiment_score=float(sentiment_score),
                        num_segments=len(topics),
                        keywords=keywords_str,
                        file_size_mb=file_size_mb
                    )
                    st.info(" Results saved to database")
                except Exception as db_err:
                    st.warning(f" Database save warning: {str(db_err)[:100]}")
                
                st.success(" Analysis complete! Explore visualizations below.")
                
            except Exception as e:
                error_msg = str(e)
                st.error(f" Analysis failed: {error_msg}")
                
                if "timeout" in error_msg.lower() or "read" in error_msg.lower():
                    st.warning("""
                    **Network Timeout:** The model downloading took too long.
                    
                    Solutions:
                    1. Check your internet connection
                    2. Try uploading a smaller file first
                    3. Run troubleshoot.py: `python troubleshoot.py`
                    4. Retry in a few moments
                    """)
                else:
                    st.warning("Check the audio file format and try again.")


# Main content areas
if not st.session_state.analysis_complete:
    st.info(" Upload an audio file and click ' Analyze Podcast' to begin")
    st.markdown("""
    ###  What This App Does:
    1. **Transcription**: Converts audio to text using AI
    2. **Segmentation**: Breaks down content into logical segments
    3. **Analysis**: Extracts keywords, sentiments, and summaries
    4. **Visualization**: Creates interactive charts and dashboards
    """)
else:
    index = st.session_state.index
    search_engine = st.session_state.search_engine
    topics = st.session_state.topics
    transcript = st.session_state.transcript
    sentiment_score = st.session_state.sentiment_score
    
    # Display overall metrics
    st.subheader(" Episode Overview")
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    with metric_col1:
        st.metric(" Total Segments", len(topics))
    with metric_col2:
        sentiment_icon = "" if sentiment_score > 0.5 else "" if sentiment_score < -0.5 else "😐"
        st.metric(f"{sentiment_icon} Avg Sentiment", f"{sentiment_score:.3f}")
    with metric_col3:
        st.metric(" Total Duration", f"{index.segments[-1]['end']:.1f}s")
    with metric_col4:
        st.metric(" Word Count", len(transcript.split()))
    
    # provide download options
    if st.session_state.get("audio_path"):
        audio_name = os.path.basename(st.session_state.audio_path)
        download_col1, download_col2 = st.columns(2)
        
        with download_col1:
            try:
                with open(st.session_state.audio_path, "rb") as af:
                    st.download_button(" Download Audio", data=af.read(), file_name=audio_name)
            except Exception:
                pass
        
        with download_col2:
            episode_id = os.path.splitext(audio_name)[0]
            segment_json = os.path.join("final_outputs", f"{episode_id}.json")
            if os.path.exists(segment_json):
                # Load JSON and remove embeddings
                with open(segment_json, "r", encoding='utf-8') as jf:
                    json_data = json.load(jf)
                
                # Remove embedding field from each segment
                if "segments" in json_data:
                    for seg in json_data["segments"]:
                        seg.pop("embedding", None)
                
                # Convert back to bytes without embeddings
                clean_json_data = json.dumps(json_data, indent=2, ensure_ascii=False).encode('utf-8')
                st.download_button(" Download Segments JSON", data=clean_json_data, 
                                     file_name=f"{episode_id}.json", mime="application/json")
    
    st.divider()
    
    # Sidebar navigation
    with st.sidebar:
        st.header(" Navigation")
        page = st.radio(
            "Choose a view:",
            [" Transcript", " Search", " Analytics", " Timeline", " Keywords", " Sentiment", " Database", " Multi-Episode Test"],
            index=0,
            help="Select a view to explore your podcast analysis"
        )

    # PAGE: Transcript
    
    if page == " Transcript":
        st.header(" Transcripts & Segments")
        
        # Tabs for transcript vs segments
        inner_tab1, inner_tab2 = st.tabs(["Full Transcript", "Segments View"])
        
        with inner_tab1:
            st.subheader(" Complete Episode Transcript")
            if transcript:
                st.write(transcript)
            else:
                st.info("No transcript available.")
        
        with inner_tab2:
            # Add controls for segments view
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            with col1:
                show_summaries = st.checkbox("Show Summaries", value=True)
            with col2:
                show_keywords = st.checkbox("Show Keywords", value=True)
            with col3:
                compact_view = st.checkbox("Compact View", value=False)
            with col4:
                show_raw = st.checkbox("Show Raw Data", value=False)
            
            # Create a scrollable container
            with st.container(height=600):
                for i, seg in enumerate(index.segments):
                    # Segment header with styling
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <strong>Segment {seg['id']}</strong> | 
                        <span style="color: #0066cc;">[{index._format_time(seg['start'])} - {index._format_time(seg['end'])}]</span> 
                        <span style="color: #666;">({seg['duration']:.1f}s)</span>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if show_raw:
                        st.code(str(seg), language='json')
                    
                    if show_summaries and seg.get('summary'):
                        st.markdown(f"Summary: {seg['summary']}")
                    
                    text_content = seg.get("segments", seg.get("text", ""))
                    if compact_view:
                        preview = text_content[:200] + "..." if len(text_content) > 200 else text_content
                        st.write(preview)
                        if len(text_content) > 200:
                            with st.expander("Read full text"):
                                st.write(text_content)
                    else:
                        st.write(text_content)
                    
                    if show_keywords and seg.get('keywords'):
                        st.markdown(f"Keywords:{', '.join(seg['keywords'])}")
                    
                    sentiment = seg.get('sentiment_score', 0)
                    if sentiment > 0.5:
                        st.success(f"😊 Positive ({sentiment:.2f})")
                    elif sentiment < -0.5:
                        st.error(f"😞 Negative ({sentiment:.2f})")
                    else:
                        st.info(f"😐 Neutral ({sentiment:.2f})")
                    
                    st.divider()
    
   
    # PAGE: Timeline
    
    elif page == " Timeline":
        st.header(" Interactive Segment Timeline")
        
        # Timeline display options
        timeline_opt1, timeline_opt2, timeline_opt3 = st.columns(3)
        with timeline_opt1:
            show_summary = st.checkbox("Show Summaries", value=True)
        with timeline_opt2:
            show_keywords = st.checkbox("Show Keywords", value=True)
        with timeline_opt3:
            show_details = st.checkbox("Show Sentiment", value=True)
        
        st.divider()
        
        # Main timeline visualization
        with st.spinner(" Generating timeline visualization..."):
            fig_timeline = create_segment_timeline(index.segments)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        st.divider()
        
        # Detailed timeline view
        st.subheader(" Timeline Details")
        
        for i, seg in enumerate(index.segments):
            col1, col2, col3 = st.columns([1, 4, 1])
            
            with col1:
                st.metric(f"Segment {seg['id']}", f"{seg['duration']:.1f}s")
            
            with col2:
                st.write(f"{index._format_time(seg['start'])} → {index._format_time(seg['end'])}")
                if show_summary and seg.get('summary'):
                    st.caption(f" {seg['summary']}")
                if show_keywords and seg.get('keywords'):
                    st.caption(f" {', '.join(seg['keywords'])}")
            
            with col3:
                if show_details:
                    sentiment_emoji = "😊" if seg['sentiment_score'] > 0.5 else "😞" if seg['sentiment_score'] < -0.5 else "😐"
                    st.metric(sentiment_emoji, f"{seg['sentiment_score']:.2f}")
            
            st.divider()
    
    
    # PAGE: Keywords & Topics
   
    elif page == " Keywords":
        st.header(" Keyword Analysis & Topics")
        
        # Collect all keywords
        all_keywords = []
        keyword_freq = {}
        keyword_segments = {}
        
        for seg in index.segments:
            for kw in seg['keywords']:
                all_keywords.append(kw)
                keyword_freq[kw] = keyword_freq.get(kw, 0) + 1
                if kw not in keyword_segments:
                    keyword_segments[kw] = []
                keyword_segments[kw].append(seg['id'])
        
        # Controls
        kw_col1, kw_col2 = st.columns([1, 3])
        with kw_col1:
            min_freq = st.slider("Min Frequency", 1, max(keyword_freq.values()) if keyword_freq else 1, 1)
        with kw_col2:
            selected_kw = st.multiselect("Filter Keywords", 
                                       sorted(keyword_freq.keys()), 
                                       default=sorted(keyword_freq.keys())[:5] if len(keyword_freq) > 5 else sorted(keyword_freq.keys()))
        
        # Filter keywords
        filtered_freq = {k: v for k, v in keyword_freq.items() if v >= min_freq and k in selected_kw}
        
        st.divider()
        
        # Row 1: Word Cloud and Bar Chart
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader(" Word Cloud")
            if filtered_freq:
                fig_wc = create_keyword_cloud(index.segments, num_keywords=30)
                st.pyplot(fig_wc)
            else:
                st.info("No keywords match the current filters.")
        
        with col2:
            st.subheader(" Top Keywords Bar Chart")
            if filtered_freq:
                fig_kw_bar = create_keyword_bar_chart(index.segments, num_keywords=15)
                st.plotly_chart(fig_kw_bar, use_container_width=True)
        
        st.divider()
        
        # Keywords per segment table
        st.subheader(" Keywords by Segment")
        df_seg_kw = []
        for seg in index.segments:
            df_seg_kw.append({
                "Segment": f"S{seg['id']}",
                "Keywords": ', '.join(seg['keywords']),
                "Count": len(seg['keywords']),
                "Duration": f"{seg['duration']:.1f}s",
                "Sentiment": f"{seg['sentiment_score']:.2f}"
            })
        
        df_seg_kw = pd.DataFrame(df_seg_kw)
        st.dataframe(df_seg_kw, use_container_width=True, 
                   column_config={
                       "Keywords": st.column_config.TextColumn("Keywords", width="large"),
                       "Count": st.column_config.NumberColumn("Count", format="%d"),
                       "Duration": st.column_config.TextColumn("Duration"),
                       "Sentiment": st.column_config.NumberColumn("Sentiment", format="%.2f")
                   })
        
        # Keyword co-occurrence
        if len(filtered_freq) > 1:
            st.divider()
            st.subheader(" Keyword Co-occurrence")
            kw_list = list(filtered_freq.keys())[:10]
            co_occurrence = {}
            
            for seg in index.segments:
                seg_kws = set(seg['keywords']) & set(kw_list)
                for kw1 in seg_kws:
                    for kw2 in seg_kws:
                        if kw1 != kw2:
                            key = tuple(sorted([kw1, kw2]))
                            co_occurrence[key] = co_occurrence.get(key, 0) + 1
            
            if co_occurrence:
                top_co = sorted(co_occurrence.items(), key=lambda x: x[1], reverse=True)[:10]
                st.write("Top keyword pairs:")
                for pair, count in top_co:
                    st.write(f"• {pair[0]} ↔ {pair[1]}: appears together in {count} segments")
    

    # PAGE: Sentiment Analysis
  
    elif page == " Sentiment":
        st.header(" Sentiment Analysis")
        
        df_sentiment = []
        for seg in index.segments:
            df_sentiment.append({
                "Segment": f"S{seg['id']}",
                "Sentiment": seg['sentiment_score'],
                "Timestamp": f"{index._format_time(seg['start'])}",
                "Duration": seg['duration'],
                "Word Count": len(seg.get("segments", seg.get("text", "")).split())
            })
        
        df_sentiment = pd.DataFrame(df_sentiment)
        
        st.divider()
        
        # Graph 1: Sentiment Trend Over Time
        st.subheader(" 1. Sentiment Trend Over Time (Line Plot)")
        fig_sentiment = create_sentiment_trend(index.segments)
        st.plotly_chart(fig_sentiment, use_container_width=True)
        
        st.divider()
        
        # Graph 2: Sentiment Score by Segment (Bar Chart)
        st.subheader(" 2. Sentiment Score per Segment (Bar Chart)")
        fig_bar = px.bar(df_sentiment, x="Segment", y="Sentiment",
                        title="Sentiment Analysis per Segment",
                        color="Sentiment",
                        color_continuous_scale="RdYlGn",
                        range_color=[-1, 1])
        fig_bar.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig_bar.update_layout(xaxis_title='Segment', yaxis_title='Sentiment Score', height=400)
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.divider()
        
        # Sentiment Summary Statistics
        st.subheader(" Sentiment Summary")
        positive_count = len(df_sentiment[df_sentiment['Sentiment'] > 0.5])
        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
        
        with stat_col1:
            st.metric("Average Sentiment", f"{df_sentiment['Sentiment'].mean():.2f}")
        with stat_col2:
            st.metric("Maximum Sentiment", f"{df_sentiment['Sentiment'].max():.2f}")
        with stat_col3:
            st.metric("Minimum Sentiment", f"{df_sentiment['Sentiment'].min():.2f}")
        with stat_col4:
            st.metric("Positive Segments", f"{positive_count}/{len(df_sentiment)}")
    
    
    # PAGE: Analytics Dashboard
  
    elif page == " Analytics":
        st.header(" Analytics Dashboard")
        
        # Create analytics DataFrame
        seg_data = []
        for seg in index.segments:
            seg_data.append({
                "Segment": f"S{seg['id']}",
                "Start": seg['start'],
                "End": seg['end'],
                "Duration": seg['duration'],
                "Sentiment": seg['sentiment_score'],
                "Keyword Count": len(seg['keywords']),
                "Word Count": len(seg.get("segments", seg.get("text", "")).split())
            })
        
        df = pd.DataFrame(seg_data)
        
        # Key metrics row
        st.subheader(" Key Metrics")
        metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
        with metric_col1:
            st.metric("Total Segments", len(df))
        with metric_col2:
            st.metric("Avg Duration", f"{df['Duration'].mean():.1f}s")
        with metric_col3:
            st.metric("Avg Sentiment", f"{df['Sentiment'].mean():.2f}")
        with metric_col4:
            st.metric("Unique Keywords", len(set([kw for seg in index.segments for kw in seg['keywords']])))
        
        st.divider()
        
        # Three essential graphs
        st.subheader(" Analytics Visualizations")
        
        # Graph 1: Segment Duration Distribution (Bar Plot)
        st.markdown("  1. Segment Duration Distribution (Bar Plot)")
        fig1 = px.bar(df, x="Segment", y="Duration", 
                    title="Duration Analysis per Segment",
                    color="Duration",
                    color_continuous_scale="Blues")
        fig1.update_layout(xaxis_title='Segment', yaxis_title='Duration (seconds)', height=400)
        st.plotly_chart(fig1, use_container_width=True)
        
        st.divider()
        
        # Graph 2: Combined Word Count and Keywords Trend (Line Chart)
        st.markdown("  2. Word Count & Keywords Trend (Combined Line Chart)")
        
        fig_combined = go.Figure()
        
        # Add Word Count line
        fig_combined.add_trace(go.Scatter(
            x=df['Segment'],
            y=df['Word Count'],
            mode='lines+markers',
            name='Word Count',
            line=dict(color='#4ECDC4', width=2),
            marker=dict(size=6)
        ))
        
        # Add Keyword Count line
        fig_combined.add_trace(go.Scatter(
            x=df['Segment'],
            y=df['Keyword Count'],
            mode='lines+markers',
            name='Keyword Count',
            line=dict(color='#FF6B6B', width=2),
            marker=dict(size=6)
        ))
        
        fig_combined.update_layout(
            title="Word Count & Keywords Trend Analysis",
            xaxis_title='Segment',
            yaxis_title='Count',
            height=400,
            hovermode='x unified',
            template='plotly_white',
            legend=dict(x=0.01, y=0.99)
        )
        st.plotly_chart(fig_combined, use_container_width=True)
        
        st.divider()
        
        # Detailed table
        st.subheader(" Detailed Segment Data")
        st.dataframe(df, use_container_width=True,
                   column_config={
                       "Segment": st.column_config.TextColumn("Segment"),
                       "Duration": st.column_config.NumberColumn("Duration (s)", format="%.1f"),
                       "Sentiment": st.column_config.NumberColumn("Sentiment", format="%.2f"),
                       "Keyword Count": st.column_config.NumberColumn("Keywords", format="%d"),
                       "Word Count": st.column_config.NumberColumn("Words", format="%d")
                   })
    
    
    # PAGE: Search
     
    elif page == " Search":
        st.header(" Search & Query Analysis")
        
        if search_engine is None:
            st.warning(" No transcript loaded. Please upload an audio file first.")
        else:
            st.markdown("""
            Search through your transcript using three methods:
            - Keyword Search: Find segments by matching text
            - Semantic Search: Find semantically similar segments
            - Combined: Hybrid approach using both methods
            """)
            
            # Search configuration
            search_col1, search_col2, search_col3 = st.columns(3)
            
            with search_col1:
                search_query = st.text_input(
                    " Enter search query:",
                    placeholder="e.g., 'machine learning', 'data science'",
                    key="search_query"
                )
            
            with search_col2:
                search_type = st.radio(
                    "Search Method:",
                    ["Keyword", "Semantic", "Combined"],
                    horizontal=True
                )
            
            with search_col3:
                num_results = st.slider(
                    "Results to show:",
                    min_value=1,
                    max_value=20,
                    value=5,
                    step=1
                )
            
            # Advanced options
            st.markdown("---")
            with st.expander(" Advanced Search Options"):
                adv_col1, adv_col2, adv_col3 = st.columns(3)
                
                with adv_col1:
                    if search_type == "Semantic":
                        threshold = st.slider(
                            "Similarity threshold:",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.3,
                            step=0.05,
                            help="Minimum similarity score to include results"
                        )
                    else:
                        threshold = 0.3
                
                with adv_col2:
                    if search_type == "Combined":
                        keyword_weight = st.slider(
                            "Keyword weight:",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.4,
                            step=0.1
                        )
                    else:
                        keyword_weight = 0.4
                
                with adv_col3:
                    if search_type == "Combined":
                        semantic_weight = st.slider(
                            "Semantic weight:",
                            min_value=0.0,
                            max_value=1.0,
                            value=0.6,
                            step=0.1
                        )
                    else:
                        semantic_weight = 0.6
            
            # Perform search
            if search_query and search_query.strip():
                st.markdown("---")
                st.subheader(f" Search Results for: \"{search_query}\"")
                
                try:
                    if search_type == "Keyword":
                        results = search_engine.keyword_search(search_query, top_k=num_results)
                        result_type = "Keyword Match"
                    elif search_type == "Semantic":
                        results = search_engine.semantic_search(
                            search_query, 
                            top_k=num_results,
                            threshold=threshold
                        )
                        result_type = "Semantic Similarity"
                    else:  # Combined
                        results = search_engine.combined_search(
                            search_query,
                            top_k=num_results,
                            keyword_weight=keyword_weight,
                            semantic_weight=semantic_weight
                        )
                        result_type = "Combined Score"
                    
                    if results:
                        # Display results count
                        if search_type == "Keyword":
                            st.success(f" Found {len(results)} matching segment(s)")
                        else:
                            st.success(f" Found {len(results)} result(s)")
                        
                        # Display each result
                        for idx, (result, score) in enumerate(results, 1):
                            result_container = st.container(border=True)
                            
                            with result_container:
                                # Header with segment info
                                header_cols = st.columns([1, 3, 2])
                                
                                with header_cols[0]:
                                    st.metric("Segment ID", result.get("id", "N/A"))
                                
                                with header_cols[1]:
                                    start_time = result.get("start", 0)
                                    end_time = result.get("end", 0)
                                    duration = result.get("duration", 0)
                                    st.metric("Time Range", f"{start_time:.1f}s - {end_time:.1f}s")
                                
                                with header_cols[2]:
                                    if search_type == "Semantic":
                                        st.metric(f"{result_type}", f"{score:.2%}")
                                    elif search_type == "Combined":
                                        st.metric(f"{result_type}", f"{score:.3f}")
                                    else:
                                        st.metric("Match Type", "Keyword")
                                
                                # Segment text
                                st.markdown("Segment Text:")
                                segment_text = result.get("segments", result.get("text", ""))
                                
                                # Highlight keyword if found
                                if search_type == "Keyword":
                                    query_lower = search_query.lower()
                                    text_lower = segment_text.lower()
                                    if query_lower in text_lower:
                                        # Simple highlighting by wrapping in markers
                                        highlighted = segment_text.replace(
                                            search_query,
                                            f"{search_query}"
                                        )
                                        st.markdown(highlighted)
                                    else:
                                        st.write(segment_text)
                                else:
                                    st.write(segment_text)
                                
                                # Metadata row
                                meta_cols = st.columns(3)
                                
                                with meta_cols[0]:
                                    keywords = result.get("keywords", [])
                                    if keywords:
                                        st.write(f"Keywords: {', '.join(keywords[:5])}")
                                
                                with meta_cols[1]:
                                    summary = result.get("summary", "N/A")
                                    if summary and summary != "N/A":
                                        st.write(f"Summary: {summary[:100]}...")
                                
                                with meta_cols[2]:
                                    sentiment = result.get("sentiment_score", 0)
                                    sentiment_label = "😊 Positive" if sentiment > 0.1 else ("😞 Negative" if sentiment < -0.1 else "😐 Neutral")
                                    st.write(f"**Sentiment:** {sentiment_label} ({sentiment:.2f})")
                    else:
                        st.info(f"ℹ No results found for '{search_query}' using {search_type} search")
                        
                        if search_type == "Semantic" and threshold > 0.5:
                            st.tip("Try lowering the similarity threshold to get more results")
                
                except Exception as e:
                    st.error(f" Search error: {str(e)}")
                    if "embedding" in str(e).lower() or "model" in str(e).lower():
                        st.info(" Semantic search requires embeddings. Try Keyword search instead.")
            else:
                st.info(" Enter a search query to get started")
    
    
    # PAGE: Multi-Episode Testing
    
    elif page == " Multi-Episode Test":
        st.header(" Multi-Episode Testing & Comparison")
        
        st.info(" This section is for testing the pipeline on multiple podcast episodes.")
        
        # Create test report
        st.subheader(" Current Episode Analysis Report")
        
        report_col1, report_col2 = st.columns(2)
        
        with report_col1:
            st.write("Segmentation Quality Assessment")
            st.write(f" Total Segments: {len(index.segments)}")
            st.write(f" Avg Segment Duration: {np.mean([s['duration'] for s in index.segments]):.1f}s")
            st.write(f" Duration Range: {min([s['duration'] for s in index.segments]):.1f}s - {max([s['duration'] for s in index.segments]):.1f}s")
        
        with report_col2:
            st.write("Keyword & Topic Analysis")
            all_kws = [kw for seg in index.segments for kw in seg['keywords']]
            st.write(f" Total Keywords Extracted: {len(all_kws)}")
            st.write(f" Unique Keywords: {len(set(all_kws))}")
            st.write(f" Avg Keywords per Segment: {len(all_kws) / len(index.segments):.1f}")
        
        st.divider()
        
        st.write("Summary Quality Assessment")
        summary_quality = []
        for i, seg in enumerate(index.segments):
            summary = seg.get('summary', '')
            quality = len(summary.split()) / max(len(seg.get("segments", "").split()), 1)
            quality_score = min(quality, 1.0)
            summary_quality.append({
                'Segment': f"S{seg['id']}",
                'Summary': summary[:100] + '...' if len(summary) > 100 else summary,
                'Quality': quality_score
            })
        
        df_quality = pd.DataFrame(summary_quality)
        
        fig_quality = px.bar(df_quality, x='Segment', y='Quality',
                            title='Summary Quality Score per Segment',
                            color='Quality',
                            color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_quality, use_container_width=True)
        
        st.divider()
        
        st.subheader("💾 Export Test Results")
        
        # Prepare comprehensive report
        report_data = {
            'Episode Analysis Report': {
                'Total Segments': len(index.segments),
                'Avg Sentiment': float(sentiment_score),
                'Total Duration': float(index.segments[-1]['end']),
                'Word Count': len(transcript.split()),
                'Unique Keywords': len(set(all_kws)),
                'Segments': [
                    {
                        'id': seg['id'],
                        'duration': float(seg['duration']),
                        'sentiment': float(seg['sentiment_score']),
                        'keywords_count': len(seg['keywords']),
                        'summary': seg.get('summary', '')
                    }
                    for seg in index.segments
                ]
            }
        }
        
        report_json = json.dumps(report_data, indent=2)
        st.download_button(
            label="📥 Download Test Report (JSON)",
            data=report_json,
            file_name="test_report.json",
            mime="application/json"
        )
    
    
    # PAGE: Database Viewer
   
    elif page == " Database":
        st.header("Audio Processing Database")
        
        st.info(" View all processed episodes, transcripts, and analysis results stored in the database")
        
        # Database Statistics
        st.subheader(" Database Statistics")
        
        db = st.session_state.database
        stats = db.get_statistics()
        
        stats_col1, stats_col2, stats_col3, stats_col4 = st.columns(4)
        
        with stats_col1:
            st.metric("Total Episodes", stats.get('total_records', 0))
        
        with stats_col2:
            st.metric("Avg Sentiment", f"{stats.get('avg_sentiment_score', 0):.3f}")
        
        with stats_col3:
            st.metric("Avg Processing Time", f"{stats.get('avg_processing_time_sec', 0):.1f}s")
        
        with stats_col4:
            st.metric("Total Storage", f"{stats.get('total_storage_mb', 0):.1f} MB")
        
        st.divider()
        
        # Search and Filter
        st.subheader(" Search & Filter")
        
        search_col1, search_col2 = st.columns([3, 1])
        
        with search_col1:
            search_query = st.text_input("Search by filename or keywords", placeholder="Enter search term...")
        
        with search_col2:
            refresh_btn = st.button(" Refresh", use_container_width=True)
        
        # Display Records
        st.subheader(" All Records")
        
        if search_query:
            records = db.search_records(search_query)
            st.write(f"Found {len(records)} matching records")
        else:
            records = db.get_all_records()
            st.write(f"Total records: {len(records)}")
        
        # Display as table
        if records:
            display_data = []
            for record in records:
                display_data.append({
                    'Serial #': record['serial_number'],
                    'Audio File': record['audio_filename'][:40],
                    'Transcript (Preview)': (record['transcript'][:50] + "...") if record['transcript'] else "N/A",
                    'Summary (Preview)': (record['summary'][:50] + "...") if record['summary'] else "N/A",
                    'Sentiment': f"{record['sentiment_score']:.3f}" if record['sentiment_score'] is not None else "N/A",
                    'Segments': record['num_segments'],
                    'Date': str(record['processing_date'])[:19]
                })
            
            df_display = pd.DataFrame(display_data)
            st.dataframe(df_display, use_container_width=True, height=400)
            
            # Expand individual records
            st.subheader(" View Full Details")
            
            record_numbers = [r['Serial #'] for r in display_data]
            selected_serial = st.selectbox(
                "Select an episode to view details:",
                record_numbers,
                format_func=lambda x: f"Episode #{x} - {records[record_numbers.index(x)]['audio_filename']}"
            )
            
            # Get full record details
            full_record = db.get_record_by_serial(selected_serial)
            
            if full_record:
                detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs(
                    ["Transcript", "Summary", "Metadata", "Keywords"]
                )
                
                with detail_tab1:
                    st.subheader("Full Transcript")
                    st.write(full_record['transcript'] or "No transcript available")
                
                with detail_tab2:
                    st.subheader("Summary")
                    st.write(full_record['summary'] or "No summary available")
                
                with detail_tab3:
                    st.subheader("Processing Details")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"Serial Number: {full_record['serial_number']}")
                        st.write(f"Filename: {full_record['audio_filename']}")
                        st.write(f"File Size: {full_record['file_size_mb']:.2f} MB")
                        st.write(f"Segments: {full_record['num_segments']}")
                    with col2:
                        st.write(f"Sentiment Score:{full_record['sentiment_score']:.4f}")
                        st.write(f"Processing Time: {full_record['processing_time_seconds']:.2f}s")
                        st.write(f"Date: {full_record['processing_date']}")
                        st.write(f"Status: {full_record['status']}")
                
                with detail_tab4:
                    st.subheader("Keywords")
                    keywords_text = full_record['keywords'] or "No keywords"
                    st.write(keywords_text)
                
                # Delete option
                st.divider()
                if st.button(f" Delete Episode #{selected_serial}", help="This action cannot be undone"):
                    if db.delete_record(selected_serial):
                        st.success(f"Episode #{selected_serial} deleted successfully")
                        st.rerun()
                    else:
                        st.error("Failed to delete episode")
        else:
            st.info("No records found in database. Process some episodes first!")
        
        # Export Options
        st.divider()
        st.subheader("💾 Export Database")
        
        export_col1, export_col2 = st.columns(2)
        
        with export_col1:
            if st.button("📥 Export to CSV", use_container_width=True):
                db.export_to_csv("audio_records_export.csv")
                with open("audio_records_export.csv", "r") as f:
                    st.download_button(
                        label="Download CSV",
                        data=f.read(),
                        file_name="audio_records_export.csv",
                        mime="text/csv"
                    )
                st.success(" Exported to CSV")
        
        with export_col2:
            if st.button("📥 Export to JSON", use_container_width=True):
                db.export_to_json("audio_records_export.json")
                with open("audio_records_export.json", "r") as f:
                    st.download_button(
                        label="Download JSON",
                        data=f.read(),
                        file_name="audio_records_export.json",
                        mime="application/json"
                    )
                st.success(" Exported to JSON")

# Footer
st.markdown("---")
st.markdown("""
###  AI Audio Transcriber
""")
