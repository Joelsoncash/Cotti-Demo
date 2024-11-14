import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import time
import os
import webbrowser
import random

class VideoRecommendation:
    def __init__(self, student_name, subject, lesson_content, timestamp):
        self.student_name = student_name
        self.subject = subject
        self.lesson_content = lesson_content
        self.timestamp = timestamp
        self.videos = []
        self.approved_videos = []
        self.status = "pending"  # pending, approved, denied

    def get_video_recommendations(self):
        # Generate YouTube embed search URLs based on subject and lesson content
        search_terms = {
            "Math": f"basic math tutorial {self.lesson_content}",
            "Science": f"science explanation {self.lesson_content}",
            "History": f"history lesson {self.lesson_content}",
            "English": f"english grammar tutorial {self.lesson_content}"
        }
        
        # Get search term for the subject, default to general search if not found
        search_term = search_terms.get(self.subject, f"educational tutorial {self.lesson_content}")
        
        # Create YouTube embed search URLs
        self.videos = [
            {
                "title": f"YouTube Search: {search_term}",
                "url": f"https://www.youtube.com/embed?listType=search&list={search_term}"
            }
        ]
        
        return True

# Rest of the code remains the same as in the previous implementation

class StudentWindow:
    def request_videos(self, recommendation):
        if recommendation.get_video_recommendations():
            self.data.add_video_request(recommendation)
            
            # Open YouTube search results in a new window
            for video in recommendation.videos:
                try:
                    # Create a new top-level window for YouTube search results
                    video_window = tk.Toplevel(self.window)
                    video_window.title(f"YouTube Search: {video['title']}")
                    video_window.geometry("800x600")
                    
                    # Create a web browser widget to display YouTube search results
                    web_frame = tk.Frame(video_window)
                    web_frame.pack(fill=tk.BOTH, expand=True)
                    
                    # Use tkinter's built-in web view (requires tkhtmlview)
                    from tkhtmlview import HTMLLabel
                    html_content = f"""
                    <iframe width="100%" height="100%" 
                            src="{video['url']}" 
                            frameborder="0" 
                            allowfullscreen>
                    </iframe>
                    """
                    html_view = HTMLLabel(web_frame, html=html_content)
                    html_view.pack(fill=tk.BOTH, expand=True)
                    
                except ImportError:
                    # Fallback to opening in default web browser if tkhtmlview is not available
                    webbrowser.open(video['url'])
                except Exception as e:
                    print(f"Error opening video {video['url']}: {e}")

# Rest of the code remains the same
