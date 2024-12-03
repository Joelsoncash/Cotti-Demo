import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import time
import os
import webbrowser
import random
import logging
import urllib.parse
import requests
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Elementary-Friendly Color Scheme
COLORS = {
    'background': '#F0F4F8',  # Soft blue-gray
    'primary': '#4CAF50',     # Friendly green
    'secondary': '#2196F3',   # Bright blue
    'accent': '#FF9800',      # Warm orange
    'text': '#000000'         # Black text
}

def extract_lesson_keywords(lesson_content):
    """Extract relevant keywords from lesson content"""
    # Common educational terms to prioritize
    educational_terms = {
        'math': ['addition', 'subtraction', 'multiplication', 'division', 'numbers', 'counting', 'geometry', 'algebra', 'fractions'],
        'science': ['experiment', 'biology', 'chemistry', 'physics', 'nature', 'animals', 'plants', 'earth', 'space'],
        'history': ['civilization', 'events', 'culture', 'timeline', 'people', 'places', 'ancient', 'modern'],
        'english': ['grammar', 'vocabulary', 'reading', 'writing', 'spelling', 'phonics', 'literature', 'comprehension']
    }
    
    # Remove common words and punctuation
    stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'])
    words = [word.strip('.,!?()[]{}":;').lower() for word in lesson_content.split()]
    
    # Extract important terms
    keywords = []
    
    # Add subject-specific educational terms that appear in the content
    for subject, terms in educational_terms.items():
        for term in terms:
            if term in words:
                keywords.append(term)
    
    # Add other significant words (longer than 3 letters, not in stop words)
    content_keywords = [word for word in words if len(word) > 3 and word not in stop_words]
    keywords.extend(content_keywords[:3])  # Add up to 3 content-specific keywords
    
    # Remove duplicates and return
    return list(set(keywords))

def scrape_elementary_youtube_links(subject, lesson_content):
    """Scrape elementary-level educational YouTube videos based on lesson content"""
    try:
        # Extract keywords from lesson content
        keywords = extract_lesson_keywords(lesson_content)
        
        # Create a specific educational search query
        grade_terms = "elementary kids"
        educational_terms = "lesson tutorial"
        keyword_string = " ".join(keywords[:3]) if keywords else ""  # Use up to 3 keywords
        
        # Build search query with proper formatting
        search_query = f"{subject} {keyword_string} {educational_terms} {grade_terms}"
        search_query = search_query.replace('"', '').replace(':', '')  # Remove special characters
        logger.info(f"Generated search query: {search_query}")
        
        # Encode the search query
        encoded_query = urllib.parse.quote(search_query)
        
        # YouTube search URL
        url = f"https://www.youtube.com/results?search_query={encoded_query}"
        
        # Send request with user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers)
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find video links with additional metadata
        video_links = []
        for link in soup.find_all('a', {'id': 'video-title'})[:10]:
            title = link.get('title', '')
            if not title:  # Skip if no title
                continue
                
            href = link.get('href', '')
            if not href or not href.startswith('/watch?v='):  # Skip if not a valid video URL
                continue
                
            # Only include videos that seem educational and appropriate for elementary level
            title_lower = title.lower()
            if any(term in title_lower for term in ['lesson', 'learn', 'education', 'tutorial', 'elementary', 'kids', 'school', 'teach']):
                video_links.append({
                    'title': title,
                    'url': f"https://www.youtube.com{href}",
                    'approved': False,
                    'subject': subject,
                    'keywords': keywords,
                    'grade_level': 'Elementary'
                })
        
        logger.info(f"Found {len(video_links)} educational videos for {subject}")
        return video_links
    except Exception as e:
        logger.error(f"Error scraping YouTube links: {e}")
        return []

class ElementaryButton(tk.Button):
    def __init__(self, parent, **kwargs):
        kwargs.setdefault('bg', COLORS['primary'])
        kwargs.setdefault('fg', 'white')
        kwargs.setdefault('font', ('Arial', 12, 'bold'))
        kwargs.setdefault('relief', tk.FLAT)
        kwargs.setdefault('padx', 20)
        kwargs.setdefault('pady', 10)
        super().__init__(parent, **kwargs)
        
        # Hover effects
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
    
    def on_enter(self, e):
        self.configure(bg=COLORS['secondary'])
    
    def on_leave(self, e):
        self.configure(bg=COLORS['primary'])

class StudentData:
    def __init__(self):
        self.responses = []
        self.video_requests = []
        self.approved_videos = {}  # Dictionary to store approved videos by student name

    def add_response(self, name, understanding, subject):
        now = datetime.now()
        self.responses.append({
            'name': name,
            'understanding': '🟢' if understanding else '🔴',
            'time': now.strftime("%I:%M%p"),
            'date': now.strftime("%m/%d/%y"),
            'subject': subject
        })
    
    def add_video_request(self, recommendation):
        self.video_requests.append(recommendation)
        
    def get_approved_videos(self, student_name):
        return self.approved_videos.get(student_name, [])
        
    def approve_video(self, student_name, video):
        if student_name not in self.approved_videos:
            self.approved_videos[student_name] = []
        self.approved_videos[student_name].append(video)

class VideoRecommendation:
    def __init__(self, student_name, subject, lesson_content, timestamp):
        self.student_name = student_name
        self.subject = subject
        self.lesson_content = lesson_content
        self.timestamp = timestamp
        self.videos = []
        self.approved_videos = []
        self.pending_videos = []
        self.status = "pending"
        self.keywords = []

    def get_video_recommendations(self):
        try:
            # Extract keywords from lesson content
            self.keywords = extract_lesson_keywords(self.lesson_content)
            
            # Get videos based on subject and lesson content
            self.pending_videos = scrape_elementary_youtube_links(self.subject, self.lesson_content)
            
            # Log the recommendations
            logger.info(f"Generated video recommendations for {self.subject}")
            logger.info(f"Keywords used: {', '.join(self.keywords)}")
            logger.info(f"Found {len(self.pending_videos)} relevant videos")
            
            return True
        except Exception as e:
            logger.error(f"Error generating video recommendations: {e}")
            return False

class StudentWindow:
    def __init__(self, parent, student_name, data):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Student View - {student_name}")
        self.window.geometry("400x600")
        self.window.configure(bg=COLORS['background'])
        
        self.student_name = student_name
        self.data = data
        self.cooldown_active = False
        self.last_response_time = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Subject Selection
        subject_frame = tk.Frame(self.window, bg=COLORS['background'])
        subject_frame.pack(fill='x', padx=20, pady=10)
        
        subject_label = tk.Label(
            subject_frame, 
            text="Choose Your Subject 📚", 
            font=('Arial', 16), 
            bg=COLORS['background'], 
            fg=COLORS['text']
        )
        subject_label.pack(side='top', anchor='w')
        
        self.subject = ttk.Combobox(
            subject_frame, 
            values=["Math 🔢", "Science 🧪", "History 🌍", "English 📖"], 
            font=('Arial', 14), 
            state="readonly"
        )
        self.subject.pack(fill='x', pady=(5, 10))
        self.subject.set("Math 🔢")
        
        # Lesson Display
        lesson_frame = tk.Frame(self.window, bg=COLORS['background'])
        lesson_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        lesson_label = tk.Label(
            lesson_frame, 
            text="Today's Lesson 📖", 
            font=('Arial', 16), 
            bg=COLORS['background'], 
            fg=COLORS['text']
        )
        lesson_label.pack(side='top', anchor='w')
        
        self.lesson_text = tk.Text(
            lesson_frame, 
            wrap=tk.WORD, 
            font=('Arial', 12), 
            bg='white', 
            height=10
        )
        self.lesson_text.pack(fill='both', expand=True, pady=(5, 10))
        self.lesson_text.config(state=tk.DISABLED)
        
        # Understanding Buttons
        button_frame = tk.Frame(self.window, bg=COLORS['background'])
        button_frame.pack(fill='x', padx=20, pady=10)
        
        understand_button = ElementaryButton(
            button_frame, 
            text="I Understand 👍", 
            command=lambda: self.handle_response(True)
        )
        understand_button.pack(side='left', expand=True, padx=5)
        
        help_button = ElementaryButton(
            button_frame, 
            text="I Need Help 🤔", 
            command=lambda: self.handle_response(False),
            bg=COLORS['accent']
        )
        help_button.pack(side='right', expand=True, padx=5)
        
        # Bind subject change to update lesson
        self.subject.bind('<<ComboboxSelected>>', self.update_lesson_content)
        
        # Initial lesson content
        self.update_lesson_content()

    def update_lesson_content(self, event=None):
        subject = self.subject.get().split()[0].lower()
        lesson_file = os.path.join("lessons", f"{subject}.txt")
        
        self.lesson_text.config(state=tk.NORMAL)
        self.lesson_text.delete(1.0, tk.END)
        
        if os.path.exists(lesson_file):
            with open(lesson_file, 'r') as file:
                content = file.read()
                self.lesson_text.insert(tk.END, content)
        else:
            self.lesson_text.insert(tk.END, "No lesson available for this subject.")
        
        self.lesson_text.config(state=tk.DISABLED)

    def handle_response(self, understanding):
        if self.cooldown_active:
            return
            
        current_time = datetime.now()
        if self.last_response_time is not None:
            time_diff = current_time - self.last_response_time
            if time_diff.total_seconds() < 180:  # 3 minutes = 180 seconds
                return
        
        self.last_response_time = current_time
        self.cooldown_active = True
        self.data.add_response(self.student_name, understanding, self.subject.get())
        
        # If student doesn't understand, request video recommendations
        if not understanding:
            # Get current lesson content
            subject = self.subject.get().split()[0]
            lesson_file = os.path.join("lessons", f"{subject.lower()}.txt")
            lesson_content = ""
            if os.path.exists(lesson_file):
                with open(lesson_file, 'r') as file:
                    lesson_content = file.read()
            
            # Create video recommendation request
            recommendation = VideoRecommendation(
                self.student_name,
                subject,
                lesson_content,
                current_time
            )
            
            # Get video recommendations in background
            threading.Thread(target=self.request_videos, args=(recommendation,), daemon=True).start()
            
            # Show approved videos if available
            self.show_approved_videos()
        
        # Start cooldown timer
        self.start_cooldown_timer()
        
    def show_approved_videos(self):
        """Show approved videos in a new window"""
        approved_videos = self.data.get_approved_videos(self.student_name)
        if approved_videos:
            video_window = tk.Toplevel(self.window)
            video_window.title("Approved Videos 🎥")
            video_window.geometry("600x400")
            video_window.configure(bg=COLORS['background'])
            
            # Create listbox for videos
            video_list = tk.Listbox(
                video_window,
                font=('Arial', 12),
                bg='white',
                selectmode=tk.SINGLE
            )
            video_list.pack(expand=True, fill='both', padx=20, pady=20)
            
            # Add videos to listbox
            for video in approved_videos:
                video_list.insert(tk.END, video['title'])
                
            # Watch button
            watch_button = ElementaryButton(
                video_window,
                text="Watch Video 🎥",
                command=lambda: self.watch_video(video_list, approved_videos)
            )
            watch_button.pack(pady=10)
            
    def watch_video(self, video_list, approved_videos):
        """Open selected video in browser"""
        selection = video_list.curselection()
        if selection:
            index = selection[0]
            video = approved_videos[index]
            webbrowser.open(video['url'])
            
    def request_videos(self, recommendation):
        if recommendation.get_video_recommendations():
            self.data.add_video_request(recommendation)
            
    def start_cooldown_timer(self):
        self.cooldown_active = True
        self.update_timer()
        
    def update_timer(self):
        if not self.cooldown_active:
            return
            
        time_diff = datetime.now() - self.last_response_time
        remaining = 180 - int(time_diff.total_seconds())
        
        if remaining <= 0:
            self.cooldown_active = False
            return
            
        mins = remaining // 60
        secs = remaining % 60

class TeacherWindow:
    def __init__(self, parent, data):
        self.window = tk.Toplevel(parent)
        self.window.title("Teacher View")
        self.window.geometry("1000x600")
        self.window.configure(bg=COLORS['background'])
        
        self.data = data
        self.create_widgets()
        
        # Start auto-refresh
        self.start_auto_refresh()
        
    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Student Progress Tab
        self.progress_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.progress_frame, text="Student Progress 📊")
        
        # Video Approval Tab
        self.video_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.video_frame, text="Video Approvals 🎥")
        
        self.setup_progress_tab()
        self.setup_video_tab()
        
    def setup_progress_tab(self):
        # Create treeview for student responses
        self.progress_tree = ttk.Treeview(
            self.progress_frame,
            columns=("Name", "Understanding", "Time", "Date", "Subject"),
            show="headings"
        )
        
        # Set column headings
        self.progress_tree.heading("Name", text="Student Name")
        self.progress_tree.heading("Understanding", text="Status")
        self.progress_tree.heading("Time", text="Time")
        self.progress_tree.heading("Date", text="Date")
        self.progress_tree.heading("Subject", text="Subject")
        
        # Set column widths
        self.progress_tree.column("Name", width=150)
        self.progress_tree.column("Understanding", width=80)
        self.progress_tree.column("Time", width=100)
        self.progress_tree.column("Date", width=100)
        self.progress_tree.column("Subject", width=150)
        
        self.progress_tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Add auto-refresh indicator
        self.refresh_label = tk.Label(
            self.progress_frame,
            text="🔄 Auto-refreshing every 2 seconds",
            font=('Arial', 10),
            fg=COLORS['secondary']
        )
        self.refresh_label.pack(pady=5)
        
    def setup_video_tab(self):
        # Create treeview for video requests
        self.video_tree = ttk.Treeview(
            self.video_frame,
            columns=("Student", "Subject", "Video Title", "Keywords", "Status"),
            show="headings"
        )
        
        # Set column headings
        self.video_tree.heading("Student", text="Student Name")
        self.video_tree.heading("Subject", text="Subject")
        self.video_tree.heading("Video Title", text="Video Title")
        self.video_tree.heading("Keywords", text="Lesson Keywords")
        self.video_tree.heading("Status", text="Status")
        
        # Set column widths
        self.video_tree.column("Student", width=150)
        self.video_tree.column("Subject", width=100)
        self.video_tree.column("Video Title", width=300)
        self.video_tree.column("Keywords", width=200)
        self.video_tree.column("Status", width=100)
        
        self.video_tree.pack(expand=True, fill="both", padx=10, pady=10)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.video_frame, orient="vertical", command=self.video_tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.video_tree.configure(yscrollcommand=scrollbar.set)
        
        # Button frame
        button_frame = tk.Frame(self.video_frame, bg=COLORS['background'])
        button_frame.pack(fill='x', padx=10, pady=5)
        
        # Preview button
        preview_button = ElementaryButton(
            button_frame,
            text="Preview Video 🎥",
            command=self.preview_video
        )
        preview_button.pack(side='left', padx=5)
        
        # Approve button
        approve_button = ElementaryButton(
            button_frame,
            text="Approve Video ✅",
            command=self.approve_video
        )
        approve_button.pack(side='left', padx=5)
        
        # Reject button
        reject_button = ElementaryButton(
            button_frame,
            text="Reject Video ❌",
            command=self.reject_video,
            bg=COLORS['accent']
        )
        reject_button.pack(side='left', padx=5)
        
        # Add refresh indicator
        self.video_refresh_label = tk.Label(
            self.video_frame,
            text="🔄 Video recommendations refresh every 2 seconds",
            font=('Arial', 10),
            fg=COLORS['secondary']
        )
        self.video_refresh_label.pack(pady=5)
    
    def preview_video(self):
        selected = self.video_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a video to preview")
            return
            
        item = self.video_tree.item(selected[0])
        student_name = item['values'][0]
        
        # Find the video request
        for request in self.data.video_requests:
            if request.student_name == student_name:
                for video in request.pending_videos:
                    if video['title'] in item['values'][2]:
                        webbrowser.open(video['url'])
                        break
                        
    def approve_video(self):
        selected = self.video_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a video to approve")
            return
            
        item = self.video_tree.item(selected[0])
        student_name = item['values'][0]
        video_title = item['values'][2]
        
        # Find the video request and approve it
        for request in self.data.video_requests:
            if request.student_name == student_name:
                for video in request.pending_videos:
                    if video['title'] == video_title:
                        video['approved'] = True
                        self.data.approve_video(student_name, video)
                        self.video_tree.set(selected[0], "Status", "Approved ✅")
                        break
                        
    def reject_video(self):
        selected = self.video_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a video to reject")
            return
            
        self.video_tree.delete(selected[0])

    def start_auto_refresh(self):
        """Start auto-refresh of student progress and video requests"""
        self.update_progress_tree()
        self.update_video_tree()
        self.window.after(2000, self.start_auto_refresh)  # Refresh every 2 seconds

    def update_progress_tree(self):
        """Update the progress tree with latest student data"""
        # Clear existing items
        for item in self.progress_tree.get_children():
            self.progress_tree.delete(item)
        
        # Add all responses
        for response in self.data.responses:
            self.progress_tree.insert(
                "",
                "end",
                values=(
                    response["name"],
                    response["understanding"],
                    response["time"],
                    response["date"],
                    response["subject"]
                )
            )
            
    def update_video_tree(self):
        """Update the video tree with latest video requests"""
        # Clear existing items
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
        
        # Add all video requests
        for request in self.data.video_requests:
            for video in request.pending_videos:
                status = "Approved ✅" if video.get('approved', False) else "Pending"
                keywords = ", ".join(request.keywords) if hasattr(request, 'keywords') else ""
                self.video_tree.insert(
                    "",
                    "end",
                    values=(
                        request.student_name,
                        request.subject,
                        video['title'],
                        keywords,
                        status
                    )
                )

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("COttie Connect")
        self.root.geometry("600x400")
        self.root.configure(bg=COLORS['background'])
        
        # Initialize student data
        self.student_data = StudentData()
        
        # Create main menu
        self.create_widgets()
        
    def create_widgets(self):
        # Welcome Label
        welcome_label = tk.Label(
            self.root,
            text="Welcome to COttie Connect! 🎓",
            font=('Arial', 24, 'bold'),
            bg=COLORS['background'],
            fg=COLORS['text']
        )
        welcome_label.pack(pady=40)
        
        # Student Login Frame
        login_frame = tk.Frame(self.root, bg=COLORS['background'])
        login_frame.pack(pady=20)
        
        name_label = tk.Label(
            login_frame,
            text="Enter Your Name:",
            font=('Arial', 14),
            bg=COLORS['background'],
            fg=COLORS['text']
        )
        name_label.pack()
        
        self.name_entry = tk.Entry(
            login_frame,
            font=('Arial', 14),
            width=30,
            relief=tk.FLAT
        )
        self.name_entry.pack(pady=10)
        
        # Buttons Frame
        button_frame = tk.Frame(self.root, bg=COLORS['background'])
        button_frame.pack(pady=20)
        
        student_button = ElementaryButton(
            button_frame,
            text="Student Login 👨‍🎓",
            command=self.open_student_window
        )
        student_button.pack(side='left', padx=10)
        
        teacher_button = ElementaryButton(
            button_frame,
            text="Teacher View 👨‍🏫",
            command=self.open_teacher_window
        )
        teacher_button.pack(side='left', padx=10)
        
        settings_button = ElementaryButton(
            button_frame,
            text="Settings ⚙️",
            command=self.open_settings
        )
        settings_button.pack(side='left', padx=10)
        
    def open_student_window(self):
        student_name = self.name_entry.get().strip()
        if not student_name:
            messagebox.showwarning("Warning", "Please enter your name first!")
            return
        
        StudentWindow(self.root, student_name, self.student_data)
        
    def open_teacher_window(self):
        TeacherWindow(self.root, self.student_data)
        
    def open_settings(self):
        SettingsWindow(self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
