# 🎬 AI Video Highlights Generator

Generate **short highlight reels** from videos (e.g., YouTube downloads) using AI + Django.  
The app extracts highlight segments around key timestamps and merges them into a single **highlight reel**.  

---

## ✨ Features
- Upload or download a video (e.g., from YouTube).
- Automatically create highlight clips around given timestamps.
- Concatenate clips into a **final highlight reel**.
- Clean and futuristic **Django web UI**.

---

## 🛠️ Installation

### 1. Clone the repo
```bash
git clone https://github.com/your-username/ai-highlights.git
cd ai-highlights
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Install FFmpeg (required)
- **macOS**: `brew install ffmpeg`  
- **Linux (Debian/Ubuntu)**: `sudo apt-get install ffmpeg`  
- **Windows**: [Download FFmpeg](https://ffmpeg.org/download.html) and add it to PATH.

---

## ▶️ Usage

### Start the Django server:
```bash
python manage.py runserver
```

### Generate highlights:
- Open [http://127.0.0.1:8000](http://127.0.0.1:8000)  
- Enter a **video URL** (e.g., YouTube) or upload a file  
- The system extracts highlights and produces `media/highlight.mp4`

---


## 📂 Project Structure
```
ai_highlights/
│
├── highlights/                 # Django app
│   ├── templates/highlights/   # HTML templates
│   ├── views.py                # Web routes
│   ├── highlight_generator.py  # MoviePy version
│   ├── utils.py                # FFmpeg version
│
├── media/                      # Generated videos
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🔮 Roadmap
- [ ] Add **automatic highlight detection** (AI-based, not just timestamps).  
- [ ] Add transitions, watermarks, text overlays.  
- [ ] Enable direct **Instagram/TikTok upload**.  
- [ ] Drag-and-drop file upload UI.  

---

## 📜 License
MIT License © 2025  
Created with ❤️ using Django.
