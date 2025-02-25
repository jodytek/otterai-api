import os
import time
import json
import asyncio
import sys
from datetime import datetime
from anthropic import Anthropic

# Path to the cloned repository
REPO_PATH = r"C:\Users\jodyt\OneDrive\Documents\GitHub\otterai-api"

# Add the repository to the path
if os.path.exists(REPO_PATH):
    sys.path.append(REPO_PATH)
else:
    print(f"Error: Repository path '{REPO_PATH}' not found.")
    print("Please clone the otterai-api repository and update the REPO_PATH variable.")
    sys.exit(1)

# Now import from the repository
try:
    from otterai import OtterAI
except ImportError:
    print("Error: Failed to import OtterAI from the repository.")
    print("Make sure you've cloned the repository correctly and updated the REPO_PATH.")
    sys.exit(1)

# Configuration
EXPORT_DIR = os.path.expanduser("~/Documents/otter_exports")
EMAIL = "jhoagland@recoverypoint.com"
PASSWORD = "TYytGHhgBNnb67"

# Claude AI configuration
ANALYZE_WITH_CLAUDE = False  # Set to True to enable Claude analysis
ANTHROPIC_API_KEY = "your-api-key-here"  # Replace with your actual API key
SUMMARIZE_PROMPT = "Please summarize the key points from this transcript. Include any important topics, decisions made, and action items."

# Ensure export directory exists
os.makedirs(EXPORT_DIR, exist_ok=True)

def get_timestamp():
    """Get current timestamp for filename."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def analyze_with_claude(transcript_text, api_key):
    """Use Claude AI to analyze transcript content."""
    try:
        anthropic_client = Anthropic(api_key=api_key)
        message = anthropic_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=1000,
            messages=[
                {"role": "user", "content": f"{SUMMARIZE_PROMPT}\n\n{transcript_text}"}
            ]
        )
        return message.content
    except Exception as e:
        print(f"Error using Claude AI: {str(e)}")
        return f"Error analyzing transcript: {str(e)}"

def extract_transcript_text(conversation_content):
    """Extract clean text from conversation content for analysis."""
    transcript_text = ""
    
    if isinstance(conversation_content, dict):
        if 'transcripts' in conversation_content:
            for transcript in conversation_content['transcripts']:
                speaker = transcript.get('speaker', '')
                text = transcript.get('text', '')
                if speaker and text:
                    transcript_text += f"{speaker}: {text}\n"
                elif text:
                    transcript_text += f"{text}\n"
    elif conversation_content:
        transcript_text = str(conversation_content)
        
    return transcript_text

async def export_conversations():
    """Export all conversations using the unofficial Otter.ai API."""
    print(f"Starting Otter.ai export to {EXPORT_DIR}...")
    
    # Initialize the OtterAI client
    client = OtterAI()
    
    try:
        # Login to Otter.ai
        print("Logging in to Otter.ai...")
        login_result = await client.login(EMAIL, PASSWORD)
        if not login_result:
            print("Login failed. Please check your credentials.")
            return
        
        # Get all conversations (notes)
        print("Fetching list of conversations...")
        conversations = await client.get_notes()
        
        if not conversations:
            print("No conversations found.")
            return
            
        print(f"Found {len(conversations)} conversations.")
        
        # Process each conversation
        for i, conversation in enumerate(conversations):
            conversation_id = conversation.get('id')
            title = conversation.get('title', 'Untitled Conversation')
            created_date = conversation.get('created_at', '')
            
            print(f"\nProcessing conversation {i+1}/{len(conversations)}: {title}")
            
            # Skip if no ID found
            if not conversation_id:
                print(f"Skipping conversation with no ID: {title}")
                continue
                
            try:
                # Export conversation content
                print(f"Exporting: {title}...")
                conversation_content = await client.get_note_content(conversation_id)
                
                # Create filename from title and date
                safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_', '-')).strip()
                safe_title = safe_title.replace(' ', '_')
                filename = f"{safe_title}_{get_timestamp()}.txt"
                filepath = os.path.join(EXPORT_DIR, filename)
                
                # Write content to file
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Save conversation metadata
                    f.write(f"Title: {title}\n")
                    f.write(f"Date: {created_date}\n")
                    f.write(f"ID: {conversation_id}\n")
                    f.write("=" * 80 + "\n\n")
                    
                    # Save the actual transcription content
                    if isinstance(conversation_content, dict):
                        # Extract transcript from response
                        if 'transcripts' in conversation_content:
                            for transcript in conversation_content['transcripts']:
                                f.write(f"{transcript.get('speaker', '')}: {transcript.get('text', '')}\n")
                        else:
                            # Save raw content if structure is unexpected
                            f.write(json.dumps(conversation_content, indent=2))
                    else:
                        # Handle any other type of content
                        f.write(str(conversation_content))
                
                print(f"Successfully exported to {filepath}")
                
                # Analyze with Claude if enabled
                if ANALYZE_WITH_CLAUDE and ANTHROPIC_API_KEY and ANTHROPIC_API_KEY != "your-api-key-here":
                    print(f"Analyzing with Claude AI: {title}...")
                    transcript_text = extract_transcript_text(conversation_content)
                    if transcript_text:
                        summary = analyze_with_claude(transcript_text, ANTHROPIC_API_KEY)
                        summary_filepath = f"{filepath}.summary.txt"
                        
                        with open(summary_filepath, 'w', encoding='utf-8') as f:
                            f.write(f"SUMMARY OF: {title}\n")
                            f.write(f"Date: {created_date}\n")
                            f.write("=" * 80 + "\n\n")
                            f.write(summary)
                            
                        print(f"Created summary at {summary_filepath}")
                    else:
                        print(f"No transcript content to analyze for {title}")
                
                # Delete code commented out for safety - uncomment when export is verified to work
                # print(f"Deleting: {title}...")
                # delete_result = await client.delete_note(conversation_id)
                # if delete_result:
                #     print(f"Successfully deleted {title}")
                # else:
                #     print(f"Failed to delete {title}")
                
                # Add a small delay between operations
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"Error processing conversation {title}: {str(e)}")
                continue
        
        print("\nProcess completed.")
        
    except Exception as e:
        print(f"Error: {str(e)}")
    
    # No need for client.close() as it doesn't exist in the OtterAI class

if __name__ == "__main__":
    # Process command line arguments
    import argparse
    
    parser = argparse.ArgumentParser(description='Export and analyze Otter.ai conversations')
    parser.add_argument('--analyze', action='store_true', help='Enable Claude AI analysis')
    parser.add_argument('--anthropic-key', help='Your Anthropic API key for Claude')
    parser.add_argument('--export-dir', help='Directory to save exported files')
    
    args = parser.parse_args()
    
    # Override defaults with command line arguments if provided
    if args.analyze:
        ANALYZE_WITH_CLAUDE = True
    if args.anthropic_key:
        ANTHROPIC_API_KEY = args.anthropic_key
    if args.export_dir:
        EXPORT_DIR = args.export_dir
        os.makedirs(EXPORT_DIR, exist_ok=True)
    
    # Execute the async function
    asyncio.run(export_conversations())