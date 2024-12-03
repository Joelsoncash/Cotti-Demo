# COttie Connect

COttie Connect is an educational application designed to help elementary school students learn through interactive lessons with teacher-approved video recommendations.

## Features

- **Student View**
  - Interactive lesson display
  - Subject selection (Math, Science, History, English)
  - Understanding feedback system
  - Access to teacher-approved educational videos

- **Teacher View**
  - Real-time student progress monitoring
  - Video approval system
  - Lesson-specific video recommendations
  - Auto-refreshing dashboard

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Joelsoncash/Cotti-Demo.git
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

You can run the application in two ways:

### 1. Direct Python Execution
```bash
python Demo.py
```

### 2. Docker Container
```bash
docker build -t cottie-connect .
docker run -e DISPLAY=host.docker.internal:0 cottie-connect
```

## Usage

1. **Student Login**
   - Enter your name
   - Select a subject
   - Read the lesson content
   - Provide understanding feedback
   - Access approved educational videos

2. **Teacher View**
   - Monitor student progress in real-time
   - Review and approve video recommendations
   - Track student understanding across subjects

## Project Structure

- `Demo.py` - Main application file
- `lessons/` - Directory containing lesson content
  - `math.txt` - Mathematics lessons
  - `science.txt` - Science lessons
  - `history.txt` - History lessons
  - `english.txt` - English lessons
- `Dockerfile` - Docker configuration
- `requirements.txt` - Python dependencies

## Features

- Real-time student progress tracking
- Automatic video recommendations based on lesson content
- Teacher approval system for educational videos
- Interactive GUI with elementary-friendly design
- Auto-refreshing dashboards
- Subject-specific lesson content
