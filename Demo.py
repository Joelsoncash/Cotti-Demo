import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
import threading
import time
import os
import openai
import json
import webbrowser

# Configure OpenAI API with the project API key
client = openai.OpenAI(
    api_key="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",
    base_url="https://api.openai.com/v1"
)

# Ensure lessons directory exists
if not os.path.exists("lessons"):
    os.makedirs("lessons")

class FlashingCircle(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, width=20, height=20, *args, **kwargs)
        self.configure(bg='white', highlightthickness=0)
        self.circle = self.create_oval(5, 5, 15, 15, fill='blue', state='hidden')
        self.is_flashing = False
        
    def start_flash(self):
        self.is_flashing = True
        self.flash()
        
    def stop_flash(self):
        self.is_flashing = False
        self.itemconfigure(self.circle, state='hidden')
        
    def flash(self):
        if not self.is_flashing:
            return
        current_state = self.itemcget(self.circle, 'state')
        new_state = 'hidden' if current_state == 'normal' else 'normal'
        self.itemconfigure(self.circle, state=new_state)
        self.after(500, self.flash)

class StudentData:
    def __init__(self):
        self.responses = []
        self.video_requests = []

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
        try:
            prompt = f"""
            A student needs help understanding this lesson in {self.subject}:
            {self.lesson_content}
            
            Please provide 10 educational YouTube video recommendations that would help explain this topic.
            Each recommendation should include a title and a URL.
            Focus on beginner-friendly, clear explanations suitable for students.
            Format your response as a valid JSON array of objects, each with 'title' and 'url' properties.
            Ensure the JSON is properly formatted with commas between objects.
            """
            
            response = client.chat.completions.create(
                model="gpt-4-turbo-preview",  # Using latest GPT-4 with web browsing
                messages=[
                    {"role": "system", "content": "You are a helpful educational assistant that recommends relevant YouTube videos. Always format your response as a valid JSON array of objects with 'title' and 'url' properties."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            print("API Response:", content)  # Debug print
            
            # Remove code block markers if present
            content = content.replace("```json", "").replace("```", "").strip()
            
            self.videos = json.loads(content)
            return True
        except Exception as e:
            print(f"Error getting recommendations: {str(e)}")
            return False

class SettingsWindow:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Settings")
        self.window.geometry("400x300")
        
        # Create settings UI
        self.create_widgets()
        
    def create_widgets(self):
        # API Key Setting
        api_frame = ttk.LabelFrame(self.window, text="OpenAI API Settings", padding=10)
        api_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(api_frame, text="API Key:").pack(anchor="w")
        self.api_key_entry = ttk.Entry(api_frame, show="*", width=40)
        self.api_key_entry.pack(fill="x", pady=5)
        self.api_key_entry.insert(0, client.api_key)
        
        # Save Button
        ttk.Button(self.window, text="Save Settings", command=self.save_settings).pack(pady=10)
        
    def save_settings(self):
        # Save API key
        global client
        client = openai.OpenAI(
            api_key=self.api_key_entry.get(),
            base_url="https://api.openai.com/v1"
        )
        messagebox.showinfo("Success", "Settings saved successfully!")
        self.window.destroy()

class StudentWindow:
    def __init__(self, parent, student_name, data):
        self.window = tk.Toplevel(parent)
        self.window.title(f"Student View - {student_name}")
        self.window.geometry("300x400")
        
        self.student_name = student_name
        self.data = data
        self.cooldown_active = False
        self.last_response_time = None
        
        self.create_widgets()
        
    def create_widgets(self):
        # Subject Selection
        ttk.Label(self.window, text="Subject:").pack(pady=5)
        self.subject = ttk.Combobox(self.window, values=["Math", "Science", "History", "English"])
        self.subject.pack(pady=5)
        self.subject.set("Math")
        
        # Understanding Status
        status_frame = ttk.Frame(self.window)
        status_frame.pack(pady=20)
        
        self.circle = FlashingCircle(status_frame)
        self.circle.pack(side="left", padx=5)
        
        ttk.Label(status_frame, text="Understanding Status").pack(side="left")
        
        # Response Buttons
        btn_frame = ttk.Frame(self.window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="I Understand", 
                  command=lambda: self.handle_response(True)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="I Need Help", 
                  command=lambda: self.handle_response(False)).pack(side="left", padx=5)
        
        # Cooldown Timer
        self.timer_label = ttk.Label(self.window, text="")
        self.timer_label.pack(pady=10)
        
        # Current Lesson Display
        lesson_frame = ttk.LabelFrame(self.window, text="Current Lesson", padding=10)
        lesson_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.lesson_text = tk.Text(lesson_frame, wrap=tk.WORD, height=8, width=30)
        self.lesson_text.pack(fill="both", expand=True)
        self.lesson_text.config(state=tk.DISABLED)
        
        # Bind subject change to update lesson
        self.subject.bind('<<ComboboxSelected>>', self.update_lesson_content)
        
        self.circle.start_flash()
        self.update_lesson_content()

    def update_lesson_content(self, event=None):
        subject = self.subject.get().lower()
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
            subject = self.subject.get()
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
        
        # Visual feedback only through circle
        self.circle.stop_flash()
        self.window.after(1000, self.circle.start_flash)
        
        # Start cooldown timer
        self.start_cooldown_timer()

    def request_videos(self, recommendation):
        if recommendation.get_video_recommendations():
            self.data.add_video_request(recommendation)
            
            # Automatically open all recommended videos
            for video in recommendation.videos:
                try:
                    webbrowser.open(video['url'])
                except Exception as e:
                    print(f"Error opening video {video['url']}: {e}")
            
    def start_cooldown_timer(self):
        self.cooldown_active = True
        self.update_timer()
        
    def update_timer(self):
        if not self.cooldown_active:
            self.timer_label.config(text="")
            return
            
        time_diff = datetime.now() - self.last_response_time
        remaining = 180 - int(time_diff.total_seconds())
        
        if remaining <= 0:
            self.cooldown_active = False
            self.timer_label.config(text="")
            return
            
        mins = remaining // 60
        secs = remaining % 60
        self.timer_label.config(text=f"Cooldown: {mins}:{secs:02d}")
        self.window.after(1000, self.update_timer)

class TeacherWindow:
    def __init__(self, parent, data):
        self.window = tk.Toplevel(parent)
        self.window.title("Teacher View")
        self.window.geometry("800x600")
        
        self.data = data
        self.create_widgets()
        
    def create_widgets(self):
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(expand=True, fill="both")
        
        # Responses Tab
        responses_frame = ttk.Frame(self.notebook)
        self.notebook.add(responses_frame, text="Student Responses")
        
        # Create treeview for responses
        self.response_tree = ttk.Treeview(responses_frame, columns=("Name", "Understanding", "Time", "Date", "Subject"))
        self.response_tree.heading("Name", text="Name")
        self.response_tree.heading("Understanding", text="Understanding")
        self.response_tree.heading("Time", text="Time")
        self.response_tree.heading("Date", text="Date")
        self.response_tree.heading("Subject", text="Subject")
        self.response_tree.pack(expand=True, fill="both")
        
        # Video Recommendations Tab
        video_frame = ttk.Frame(self.notebook)
        self.notebook.add(video_frame, text="Video Recommendations")
        
        # Create treeview for video requests
        self.video_tree = ttk.Treeview(video_frame, columns=("Student", "Subject", "Time", "Status"))
        self.video_tree.heading("Student", text="Student")
        self.video_tree.heading("Subject", text="Subject")
        self.video_tree.heading("Time", text="Time")
        self.video_tree.heading("Status", text="Status")
        self.video_tree.pack(expand=True, fill="both")
        
        # Lesson Management Tab
        lesson_frame = ttk.Frame(self.notebook)
        self.notebook.add(lesson_frame, text="Lesson Management")
        
        # Subject selection for lessons
        subject_frame = ttk.Frame(lesson_frame)
        subject_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(subject_frame, text="Subject:").pack(side="left")
        self.lesson_subject = ttk.Combobox(subject_frame, values=["Math", "Science", "History", "English"])
        self.lesson_subject.pack(side="left", padx=5)
        self.lesson_subject.set("Math")
        
        # Lesson content
        content_frame = ttk.LabelFrame(lesson_frame, text="Lesson Content", padding=10)
        content_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.lesson_text = tk.Text(content_frame, wrap=tk.WORD)
        self.lesson_text.pack(fill="both", expand=True)
        
        # Lesson management buttons
        btn_frame = ttk.Frame(lesson_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Upload Lesson File", 
                  command=self.upload_lesson).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Save Lesson", 
                  command=self.save_lesson).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Clear", 
                  command=self.clear_lesson).pack(side="left", padx=5)
        
        self.video_tree.bind("<Double-1>", self.show_video_details)
        
        # Bind subject change to update lesson content
        self.lesson_subject.bind('<<ComboboxSelected>>', self.load_lesson_content)
        
        # Refresh button
        ttk.Button(self.window, text="Refresh", command=self.refresh_data).pack(pady=5)
        
        # Initial data load
        self.refresh_data()
        self.load_lesson_content()
        
    def upload_lesson(self):
        file_path = filedialog.askopenfilename(
            title="Select Lesson File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r') as file:
                    content = file.read()
                    self.lesson_text.delete(1.0, tk.END)
                    self.lesson_text.insert(tk.END, content)
                messagebox.showinfo("Success", "Lesson file loaded successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def save_lesson(self):
        subject = self.lesson_subject.get().lower()
        content = self.lesson_text.get(1.0, tk.END).strip()
        
        if not content:
            messagebox.showwarning("Warning", "Please enter lesson content before saving.")
            return
            
        try:
            with open(os.path.join("lessons", f"{subject}.txt"), 'w') as file:
                file.write(content)
            messagebox.showinfo("Success", "Lesson saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save lesson: {str(e)}")
    
    def clear_lesson(self):
        self.lesson_text.delete(1.0, tk.END)
    
    def load_lesson_content(self, event=None):
        subject = self.lesson_subject.get().lower()
        lesson_file = os.path.join("lessons", f"{subject}.txt")
        
        self.lesson_text.delete(1.0, tk.END)
        
        if os.path.exists(lesson_file):
            try:
                with open(lesson_file, 'r') as file:
                    content = file.read()
                    self.lesson_text.insert(tk.END, content)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load lesson: {str(e)}")
    
    def refresh_data(self):
        # Clear existing items
        for item in self.response_tree.get_children():
            self.response_tree.delete(item)
        for item in self.video_tree.get_children():
            self.video_tree.delete(item)
            
        # Load responses
        for response in self.data.responses:
            self.response_tree.insert("", "end", values=(
                response["name"],
                response["understanding"],
                response["time"],
                response["date"],
                response["subject"]
            ))
            
        # Load video requests
        for request in self.data.video_requests:
            self.video_tree.insert("", "end", values=(
                request.student_name,
                request.subject,
                request.timestamp.strftime("%I:%M%p %m/%d/%y"),
                request.status
            ))
            
    def show_video_details(self, event):
        item = self.video_tree.selection()[0]
        request_index = self.video_tree.index(item)
        request = self.data.video_requests[request_index]
        
        # Create video details window
        details_window = tk.Toplevel(self.window)
        details_window.title("Video Recommendations")
        details_window.geometry("600x400")
        
        # Show video list
        for i, video in enumerate(request.videos):
            frame = ttk.Frame(details_window)
            frame.pack(fill="x", padx=5, pady=2)
            
            ttk.Label(frame, text=f"{i+1}. {video['title']}").pack(side="left")
            ttk.Button(frame, text="Open", 
                      command=lambda url=video['url']: webbrowser.open(url)).pack(side="right")
        
        # Approval buttons
        btn_frame = ttk.Frame(details_window)
        btn_frame.pack(pady=10)
        
        ttk.Button(btn_frame, text="Approve All", 
                  command=lambda: self.approve_videos(request, details_window)).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Deny", 
                  command=lambda: self.deny_videos(request, details_window)).pack(side="left", padx=5)
                  
    def approve_videos(self, request, window):
        request.status = "approved"
        request.approved_videos = request.videos
        window.destroy()
        self.refresh_data()
        
    def deny_videos(self, request, window):
        request.status = "denied"
        request.approved_videos = []
        window.destroy()
        self.refresh_data()

class LoginApp:
    def __init__(self, root):
        self.root = root
        self.root.title("COttie Connect")
        self.root.geometry("300x200")
        
        self.data = StudentData()
        self.create_widgets()
        
    def create_widgets(self):
        # Name Entry
        ttk.Label(self.root, text="Name:").pack(pady=5)
        self.name_entry = ttk.Entry(self.root)
        self.name_entry.pack(pady=5)
        
        # Role Selection
        ttk.Label(self.root, text="Role:").pack(pady=5)
        self.role = ttk.Combobox(self.root, values=["Student", "Teacher"])
        self.role.pack(pady=5)
        self.role.set("Student")
        
        # Login Button
        ttk.Button(self.root, text="Login", command=self.login).pack(pady=20)
        
        # Settings Button
        ttk.Button(self.root, text="Settings", command=self.open_settings).pack(pady=5)
        
    def login(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter your name")
            return
            
        if self.role.get() == "Student":
            StudentWindow(self.root, name, self.data)
        else:
            TeacherWindow(self.root, self.data)
            
    def open_settings(self):
        SettingsWindow(self.root)

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
