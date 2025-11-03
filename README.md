# 🧠 VIT Exam Portal

A full-stack web application for conducting timed quizzes with review, navigation, scoring, and result analysis — built using **Flask**, **HTML/CSS**, and **JSON**.

This project was developed as part of the **First Semester Python course** at **Vellore Institute of Technology (VIT)**. It demonstrates core Python skills including:

- Flask-based web development
- JSON data handling
- Session management
- UI/UX design with Jinja templates
- Real-time quiz logic and scoring

It fulfills the requirements for a practical, hands-on Python application with real-world relevance and deployability.

## 🚀 Features

- ✅ User login with username
- ✅ Subject-based quiz selection
- ✅ Timer per question with auto-submit
- ✅ Navigation: Next, Back, Skip, Mark for Review
- ✅ Review screen with jump-to-question
- ✅ Final result with answer breakdown
- ✅ Score history and leaderboard (optional)

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, Jinja2
- **Data**: JSON files (`questions.json`, `users.json`, `leaderboard.json`)
- **Deployment**: Render (via Gunicorn)

## 🧪 Local Setup

```bash
git clone https://github.com/your-username/exam_portal.git
cd exam_portal
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python app.py

Visit http://localhost:5000

