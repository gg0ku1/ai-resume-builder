<p align="center">
  <a href="Screenshots/gif.gif">
    <img src="Screenshots/gif.gif" width="900" alt="AI Resume Builder Demo">
  </a>
</p>

<h1 align="center">🤖 AI Resume Builder</h1>

<p align="center">
An AI-powered Resume Builder built with <b>Flask</b> and <b>Google Gemini AI</b> that generates professional, ATS-friendly resumes from simple user inputs and exports them as beautifully formatted PDFs.
</p>

<p align="center">

![Python](https://img.shields.io/badge/Python-3.12-blue)
![Flask](https://img.shields.io/badge/Flask-Web%20Framework-black)
![Gemini](https://img.shields.io/badge/Google-Gemini-orange)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED)
![License](https://img.shields.io/badge/License-MIT-green)

</p>

---

# 📖 Overview

AI Resume Builder is a full-stack Flask web application that leverages **Google Gemini AI** to transform basic user inputs into professionally written, ATS-friendly resume content.

The application intelligently enhances professional summaries, technical skills, projects, work experience, and career objectives while allowing users to review and edit every AI-generated section before exporting the final resume as a print-ready PDF.

The project has also been **Dockerized**, making setup and deployment simple and consistent across different environments.

---

# ✨ Features

- 🤖 AI-powered resume generation using Google Gemini
- 📝 Professional Summary generation
- 💼 AI-enhanced work experience descriptions
- 🚀 Intelligent skill enhancement
- 🎯 Career Objective generation
- 📚 Education formatting
- 👤 Optional profile picture upload
- ✏️ Edit AI-generated content before finalizing
- 📄 Export professionally formatted PDF resumes
- 📱 Responsive user interface
- 🔐 Environment variable configuration
- 🐳 Docker support

---

# 🛠 Tech Stack

| Category | Technologies |
|-----------|--------------|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript, Jinja2 |
| AI | Google Gemini API |
| PDF Generation | WeasyPrint |
| Configuration | python-dotenv |
| Containerization | Docker, Docker Compose |

---

# 🏗️ System Architecture

```
                    +-----------------------+
                    |      Web Browser      |
                    +-----------+-----------+
                                |
                                |
                        Flask Application
                                |
        +-----------------------+-----------------------+
        |                                               |
        |                                               |
 Google Gemini API                               HTML Templates
        |                                               |
 AI-generated Resume Content                    Resume Preview
                                                        |
                                                        |
                                                  WeasyPrint
                                                        |
                                                        |
                                                  PDF Resume
```

---

# 📂 Project Structure

```
AI-Resume-Builder/
│
├── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .dockerignore
├── .gitignore
├── .env.example
├── README.md
│
├── static/
│   ├── css/
│   ├── js/
│   ├── uploads/
│   └── images/
│
├── templates/
│
├── temp_data/
│
└── Screenshots/
```

---

# ⚙️ Local Installation

### 1. Clone the repository

```bash
git clone https://github.com/gg0ku1/ai-resume-builder.git

cd ai-resume-builder
```

---

### 2. Create a virtual environment

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux / macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 4. Create a `.env` file

```env
GEMINI_API_KEY=your_api_key
GEMINI_MODEL=gemini-2.5-flash
SECRET_KEY=your_secret_key
```

---

### 5. Run the application

```bash
python app.py
```

Open:

```
http://localhost:5000
```

---

# 🐳 Running with Docker

Build and start the application:

```bash
docker compose up --build
```

Visit:

```
http://localhost:5000
```

To stop the application:

```bash
docker compose down
```

---

# 🚀 How It Works

1. Enter your personal and professional details.
2. Upload a profile picture (optional).
3. Submit the form.
4. Google Gemini AI enhances your resume content.
5. Review and edit the generated sections.
6. Preview the final resume.
7. Export it as a professional PDF.

---

# 📸 Screenshots

## 🏠 Home Page

![](Screenshots/Screenshot1.png)

---

## 📝 Resume Form

![](Screenshots/Screenshot2.png)

---

## 🤖 AI Generated Content

![](Screenshots/Screenshot3.png)

---

## 👀 Resume Preview

![](Screenshots/Screenshot4.png)

---

## 📄 Final PDF Preview

![](Screenshots/Screenshot5.png)

---

# 🔮 Future Improvements

- Multiple resume templates
- Migration to the latest Google GenAI SDK
- User authentication
- Resume version history
- Database integration
- Cloud deployment (AWS / Azure)
- CI/CD with GitHub Actions
- Production deployment using Gunicorn and Nginx

---

# 👨‍💻 Author

**Gokul**

GitHub: https://github.com/gg0ku1

---

# 📄 License

This project is licensed under the **MIT License**.