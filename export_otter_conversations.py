import os
import time
import json
import asyncio
import sys
from datetime import datetime

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

# Ensure export directory exists
os.makedirs(EXPORT_DIR, exist_ok=True)

def get_timestamp():
    """Get current timestamp for filename."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")

async def export_conversations():
    """Export all conversations using the unofficial Otter.ai API."""
    print(f"Starting Otter.ai export to {EXPORT_DIR}...")
    
    # Initialize the OtterAI client
    client = OtterAI()
    
    try:
        # Login to Otter.ai
        print("Logging in to Otter.ai...")
        await client.login(EMAIL, PASSWORD)
        
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
    
    finally:
        # Logout/cleanup
        await client.close()
        print("Logged out and closed connection.")

if __name__ == "__main__":
    # Execute the async function
    asyncio.run(export_conversations())