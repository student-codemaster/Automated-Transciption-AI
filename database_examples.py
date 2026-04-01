from database import AudioDatabase
import os

def example_1_save_record():
    """Example 1: Save a record to database"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Saving a Record to Database")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    
    # Save a sample record
    success = db.save_record(
        audio_filename="podcast_episode_1.mp3",
        audio_path="data/podcast_episode_1.mp3",
        transcript="The podcast discusses artificial intelligence, machine learning, and deep learning...",
        summary="Discussion about AI technologies and their applications in business",
        sentiment_score=0.85,
        num_segments=8,
        keywords="AI, machine learning, deep learning, neural networks, business",
        file_size_mb=45.3,
        processing_time=240.5
    )
    
    if success:
        print("Record saved successfully!")
    else:
        print("Record might already exist")


def example_2_view_all_records():
    """Example 2: View all records in database"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Viewing All Records")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    
    # Print database contents
    db.print_database(limit=5)
    
    # Or get as list
    records = db.get_all_records()
    print(f"Total records in database: {len(records)}\n")


def example_3_search_records():
    """Example 3: Search records"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Searching Records")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    
    # Search by keyword
    search_term = "AI"
    results = db.search_records(search_term)
    
    print(f"Found {len(results)} episodes matching '{search_term}':\n")
    
    for record in results:
        print(f"{record['audio_filename']}")
        print(f"Sentiment: {record['sentiment_score']:.3f}")
        print(f"Keywords: {record['keywords'][:60]}...")


def example_4_get_statistics():
    """Example 4: View database statistics"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Database Statistics")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    stats = db.get_statistics()
    
    print(f"\nDatabase Statistics:")
    print(f"Total episodes processed: {stats['total_records']}")
    print(f"Average sentiment score: {stats['avg_sentiment_score']:.3f}")
    print(f"Average processing time: {stats['avg_processing_time_sec']:.2f} seconds")
    print(f"Total storage used: {stats['total_storage_mb']:.2f} MB")


def example_5_get_single_record():
    """Example 5: Get specific record details"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Get Specific Record Details")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    
    # Get first record
    record = db.get_record_by_serial(1)
    
    if record:
        print(f"\nEpisode #{record['serial_number']}:")
        print(f"Filename: {record['audio_filename']}")
        print(f"Sentiment: {record['sentiment_score']:.4f}")
        print(f"Segments: {record['num_segments']}")
        print(f"File Size: {record['file_size_mb']:.2f} MB")
        print(f"Processing Time: {record['processing_time_seconds']:.2f} seconds")
        print(f"Date: {record['processing_date']}")
        print(f"\nTranscript Preview:")
        print(f"{record['transcript'][:150]}...")
    else:
        print("No record found with serial number 1")


def example_6_export_data():
    """Example 6: Export data to CSV and JSON"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Exporting Data")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    
    # Export to CSV
    print("\nExporting to CSV...")
    success_csv = db.export_to_csv("episodes_export.csv")
    if success_csv:
        print("Exported to: episodes_export.csv")
    
    # Export to JSON
    print("\nExporting to JSON...")
    success_json = db.export_to_json("episodes_export.json")
    if success_json:
        print("Exported to: episodes_export.json")


def example_7_update_workflow():
    """Example 7: Complete workflow - like in Streamlit app"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Complete Workflow (Like Streamlit App)")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    
    print("\nUser uploads 'episode_42.mp3'")
    print("Pipeline processes it...")
    print("Results automatically saved to database")
    
    # Simulate pipeline results
    pipeline_results = {
        "filename": "episode_42.mp3",
        "path": "data/episode_42.mp3",
        "transcript": "Long transcript here...",
        "summary": "Episode summary here...",
        "sentiment": 0.65,
        "segments": 10,
        "keywords": "technology, innovation, startup"
    }
    
    # Save like the Streamlit app does
    db.save_record(
        audio_filename=pipeline_results['filename'],
        audio_path=pipeline_results['path'],
        transcript=pipeline_results['transcript'],
        summary=pipeline_results['summary'],
        sentiment_score=pipeline_results['sentiment'],
        num_segments=pipeline_results['segments'],
        keywords=pipeline_results['keywords']
    )
    
    print("\nUser goes to 'Database' page")
    print("Sees new episode in table")
    print("Can click to view full details")
    
    # Show what user sees
    record = db.get_record_by_filename("episode_42.mp3")
    if record:
        print("\nWhat's displayed in Database page:")
        print(f"Serial #: {record['serial_number']}")
        print(f"File: {record['audio_filename']}")
        print(f"Sentiment: {record['sentiment_score']:.3f}")
        print(f"Segments: {record['num_segments']}")
        print(f"Keywords: {record['keywords']}")


def example_8_delete_record():
    """Example 8: Delete a record"""
    print("\n" + "="*70)
    print("EXAMPLE 8: Deleting a Record")
    print("="*70)
    
    db = AudioDatabase("audio_database.db")
    
    # Show records before
    records_before = len(db.get_all_records())
    print(f"Records before: {records_before}")
    
    # Delete last record (if exists)
    if records_before > 0:
        last_record = db.get_all_records()[0]
        print(f"Deleting: {last_record['audio_filename']}")
        
        success = db.delete_record(last_record['serial_number'])
        
        if success:
            records_after = len(db.get_all_records())
            print(f"Deleted successfully!")
            print(f"Records after: {records_after}")


if __name__ == "__main__":
    print("\n" + "#"*70)
    print("#  DATABASE USAGE EXAMPLES")
    print("#"*70)
    
    print("\nChoose which example to run:")
    print("1. Save a record")
    print("2. View all records")
    print("3. Search records")
    print("4. View statistics")
    print("5. Get specific record")
    print("6. Export data")
    print("7. Complete workflow")
    print("8. Delete a record")
    print("0. Run all examples")
    
    choice = input("\nEnter choice (0-8): ").strip()
    
    if choice == "1":
        example_1_save_record()
    elif choice == "2":
        example_2_view_all_records()
    elif choice == "3":
        example_3_search_records()
    elif choice == "4":
        example_4_get_statistics()
    elif choice == "5":
        example_5_get_single_record()
    elif choice == "6":
        example_6_export_data()
    elif choice == "7":
        example_7_update_workflow()
    elif choice == "8":
        example_8_delete_record()
    elif choice == "0":
        example_1_save_record()
        example_2_view_all_records()
        example_3_search_records()
        example_4_get_statistics()
        example_5_get_single_record()
        example_6_export_data()
        example_7_update_workflow()
    else:
        print("Invalid choice")
    
    print("\n" + "#"*70 + "\n")
