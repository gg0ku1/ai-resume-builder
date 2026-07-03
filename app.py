from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
import os
from werkzeug.utils import secure_filename
import google.generativeai as genai
from dotenv import load_dotenv
import uuid
import json
import shutil
import io
import datetime

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Load environment variables
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini AI
# Change GEMINI_MODEL in your .env to switch models, e.g.:
#   gemini-2.0-flash  (latest, fast)
#   gemini-1.5-flash  (stable, efficient)
#   gemini-1.5-pro    (more capable, slower)
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel(GEMINI_MODEL)
# Shorter timeout so failures are fast (default is 60s which hangs forever)
REQUEST_TIMEOUT = int(os.getenv("GEMINI_TIMEOUT", "20"))

# File upload settings
UPLOAD_FOLDER = 'static/uploads/'
TEMP_DATA_FOLDER = 'temp_data/'
DEFAULT_PROFILE_PIC = 'static/images/default-profile.png'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['TEMP_DATA_FOLDER'] = TEMP_DATA_FOLDER
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Create required directories
for folder in [UPLOAD_FOLDER, TEMP_DATA_FOLDER, 'static/images']:
    os.makedirs(folder, exist_ok=True)

# Create a default profile image placeholder if none exists
if not os.path.exists(DEFAULT_PROFILE_PIC):
    for source in ['static/default-profile.png', 'static/img/default-profile.png']:
        if os.path.exists(source):
            shutil.copy(source, DEFAULT_PROFILE_PIC)
            break

# ── Context processor ──────────────────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {'current_year': datetime.datetime.now().year}


# ── Helpers ────────────────────────────────────────────────────────────────────
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def save_data_to_file(data, prefix):
    """Persist data dict to a JSON temp file; return filename."""
    filename = f"{prefix}_{uuid.uuid4()}.json"
    filepath = os.path.join(app.config['TEMP_DATA_FOLDER'], filename)
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f)
        return filename
    except Exception as e:
        app.logger.error(f"Could not save data: {e}")
        return None


def load_data_from_file(filename):
    """Load a JSON temp file; return dict or None."""
    if not filename:
        return None
    filepath = os.path.join(app.config['TEMP_DATA_FOLDER'], filename)
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        app.logger.error(f"Could not load data from {filepath}: {e}")
    return None


# ── Demo data ─────────────────────────────────────────────────────────────────
DEMO_RESUME = {
    'name': 'Arjun Mehta',
    'email': 'arjun.mehta@email.com',
    'phone': '+91 98765 43210',
    'links': 'linkedin.com/in/arjunmehta, github.com/arjunmehta',
    'profile': '',   # leave blank so AI generates it
    'experience': (
        'Google India | Software Engineer | July 2023 – Present\n'
        'Worked on Search infrastructure; optimised indexing pipeline reducing latency by 35%.\n'
        'Built internal tooling used by 200+ engineers; saved ~4 hours per engineer per week.\n\n'
        'Infosys | Software Developer Intern | Jan 2023 – June 2023\n'
        'Developed REST APIs using Python Flask and PostgreSQL for an HR management product.\n'
        'Wrote unit tests achieving 90% coverage; reduced production bugs by 40%.'
    ),
    'projects': (
        'AI Resume Builder\n'
        'Built a full-stack web app (Flask + Gemini API) that generates AI-enhanced resumes.\n'
        'Tech: Python, Flask, Google Gemini 2.0 Flash, HTML/CSS/JS\n\n'
        'E-Commerce Price Tracker\n'
        'Scraped 5 major e-commerce sites and sent price-drop alerts via email/Telegram.\n'
        'Tech: Python, BeautifulSoup, Celery, Redis, Docker'
    ),
    'education': (
        'VJTI Mumbai | B.Tech Computer Engineering | 2023\n'
        'CGPA: 8.7 / 10  |  Department Rank: 3\n\n'
        'Delhi Public School | HSC (Science) | 2019\n'
        'Percentage: 94.2%'
    ),
    'skills': (
        'Python, Java, JavaScript, TypeScript, SQL\n'
        'Flask, FastAPI, React, Node.js\n'
        'PostgreSQL, MongoDB, Redis\n'
        'Docker, Kubernetes, Git, CI/CD\n'
        'Communication, Problem Solving, Team Leadership'
    ),
    'job_preferences': 'Seeking a Software Engineer role at a product-based company focused on scalable backend systems and AI/ML applications.',
    'image_path': 'images/default-profile.png',
    'dynamic_sections': {},
}


# ── Routes ─────────────────────────────────────────────────────────────────────
@app.route('/')
def home():
    return render_template('home.html')


@app.route('/demo')
def demo():
    """Load demo data and try real AI — falls back to pre-written content if API is unavailable."""

    # Pre-written AI-quality fallback (used if Gemini API is unreachable)
    DEMO_AI_FALLBACK = {
        'profile': {
            'content': (
                'Results-driven Software Engineer with 1+ year of experience building scalable backend systems '
                'at Google India and a strong foundation in full-stack development. '
                'Proven ability to optimise high-traffic infrastructure, reduce system latency by 35%, '
                'and deliver developer tooling adopted by 200+ engineers. '
                'Passionate about AI/ML applications, clean code, and system design. '
                'Seeking to leverage expertise in Python, distributed systems, and cloud technologies '
                'to build impactful products at scale.'
            ),
            'suggestions': 'Personalize with a specific career achievement or the company you are targeting.'
        },
        'skills': {
            'content': (
                'Technical Skills\n'
                '• Languages: Python, Java, JavaScript, TypeScript, SQL\n'
                '• Frameworks: Flask, FastAPI, React, Node.js\n'
                '• Databases: PostgreSQL, MongoDB, Redis\n'
                '• DevOps & Tools: Docker, Kubernetes, Git, CI/CD pipelines\n\n'
                'Soft Skills\n'
                '• Communication, Problem Solving, Team Leadership, Agile Collaboration'
            ),
            'suggestions': 'Prioritize skills most relevant to your target role.'
        },
        'experience': {
            'content': (
                'Google India | Software Engineer | July 2023 – Present\n'
                '• Optimised Search indexing pipeline, reducing latency by 35% across production traffic.\n'
                '• Architected internal tooling adopted by 200+ engineers, saving ~4 hrs/engineer/week.\n'
                '• Collaborated cross-functionally on high-availability service architecture.\n\n'
                'Infosys | Software Developer Intern | Jan 2023 – June 2023\n'
                '• Built 12 REST API endpoints (Flask + PostgreSQL) for an HR management platform.\n'
                '• Achieved 90% test coverage with pytest; reduced production bugs by 40%.\n'
                '• Participated in Agile sprints and daily standups.'
            ),
            'suggestions': "Quantify achievements wherever possible (e.g., '40% faster', '3x throughput')."
        },
        'projects': {
            'content': (
                'AI Resume Builder\n'
                '• End-to-end Flask app using Gemini API to generate AI-enhanced resume sections.\n'
                '• Features: session-based flow, WeasyPrint PDF export, side-by-side AI editor.\n'
                '• Tech: Python, Flask, Gemini API, HTML/CSS/JS\n\n'
                'E-Commerce Price Tracker\n'
                '• Scraped 5 e-commerce platforms; sent price-drop alerts via email and Telegram.\n'
                '• Async tasks with Celery + Redis; containerized with Docker.\n'
                '• Tech: Python, BeautifulSoup, Celery, Redis, Docker'
            ),
            'suggestions': 'Add GitHub/live demo links to make projects verifiable.'
        },
        'education': {
            'content': (
                'VJTI Mumbai | B.Tech Computer Engineering | 2023\n'
                'CGPA: 8.7 / 10  |  Dept. Rank: 3  |  Coursework: OS, DBMS, Networks, ML\n\n'
                'Delhi Public School | HSC (Science — PCM + CS) | 2019\n'
                'Percentage: 94.2%'
            ),
            'suggestions': 'Include GPA (if 3.5+/8.0+), relevant coursework, or academic honours.'
        },
        'job_preferences': {
            'content': (
                'To secure a Software Engineer position at a product-focused company where I can apply '
                'expertise in scalable backend systems, distributed architecture, and AI/ML '
                'to build impactful products at scale.'
            ),
            'suggestions': 'Keep your objective specific — mention the type of role and industry.'
        },
    }

    # Try real Gemini AI first; fall back to pre-written content on any error
    used_ai = False
    try:
        ai_sections = generate_ai_content(
            DEMO_RESUME['name'],
            DEMO_RESUME['skills'],
            DEMO_RESUME['experience'],
            DEMO_RESUME['education'],
            DEMO_RESUME['job_preferences'],
            projects=DEMO_RESUME['projects'],
            profile=DEMO_RESUME['profile'],
        )
        used_ai = True
    except Exception as e:
        app.logger.warning(f"Demo: Gemini unavailable ({e}), using pre-written fallback.")
        ai_sections = DEMO_AI_FALLBACK

    session['resume_filename']      = save_data_to_file(DEMO_RESUME, 'resume')
    session['ai_sections_filename'] = save_data_to_file(ai_sections, 'ai')

    if used_ai:
        flash('✨ Demo loaded with live Gemini AI content.', 'success')
    else:
        flash('⚡ Demo loaded with pre-written content (Gemini API unavailable — check your network/API key).', 'warning')

    return redirect(url_for('handler'))



@app.route('/form', methods=['GET', 'POST'])
def form():
    if request.method == 'POST':
        name          = request.form.get('name', '').strip()
        email         = request.form.get('email', '').strip()
        phone         = request.form.get('phone', '').strip()
        links         = request.form.get('links', '').strip()
        education     = request.form.get('education', '').strip()
        job_preferences = request.form.get('job_preferences', '').strip()
        skills        = request.form.get('skills', '').strip()
        experience    = request.form.get('experience', '').strip()
        projects      = request.form.get('projects', '').strip()
        profile_text  = request.form.get('profile', '').strip()

        # Collect dynamic (custom) sections added by the user
        dynamic_sections = {}
        for key in request.form:
            if key.startswith('dynamic_section_title_'):
                sid = key[len('dynamic_section_title_'):]
                title   = request.form.get(f'dynamic_section_title_{sid}', '')
                content = request.form.get(f'dynamic_section_{sid}', '')
                if title.strip():
                    dynamic_sections[sid] = {'title': title, 'content': content}

        # Build resume data dict
        resume_data = {
            'name': name,
            'email': email,
            'phone': phone,
            'links': links,
            'education': education,
            'job_preferences': job_preferences,
            'skills': skills,
            'experience': experience,
            'projects': projects,
            'profile': profile_text,
            'dynamic_sections': dynamic_sections,
            'image_path': DEFAULT_PROFILE_PIC.replace('static/', ''),
        }

        # Handle profile picture upload
        if 'profile_picture' in request.files:
            image = request.files['profile_picture']
            if image and image.filename and allowed_file(image.filename):
                filename = secure_filename(f"{uuid.uuid4()}_{image.filename}")
                full_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                image.save(full_path)
                resume_data['image_path'] = f"uploads/{filename}"

        # Generate AI-enhanced sections
        ai_sections = generate_ai_content(
            name, skills, experience, education, job_preferences,
            projects=projects, profile=profile_text
        )

        # Persist to temp files; store only filenames in session
        session['resume_filename']     = save_data_to_file(resume_data, 'resume')
        session['ai_sections_filename'] = save_data_to_file(ai_sections, 'ai')

        return redirect(url_for('handler'))

    return render_template('index.html')


@app.route('/handler', methods=['GET', 'POST'])
def handler():
    if 'resume_filename' not in session or 'ai_sections_filename' not in session:
        flash('Please fill out the form first.')
        return redirect(url_for('form'))

    resume_data = load_data_from_file(session['resume_filename'])
    ai_sections = load_data_from_file(session['ai_sections_filename'])

    if not resume_data or not ai_sections:
        flash('Error loading your data. Please try again.')
        return redirect(url_for('form'))

    if request.method == 'POST':
        # Rebuild resume data from the handler's edited form fields
        updated = {
            'name':            request.form.get('name', resume_data.get('name', '')),
            'email':           request.form.get('email', resume_data.get('email', '')),
            'phone':           request.form.get('phone', resume_data.get('phone', '')),
            'links':           request.form.get('links', resume_data.get('links', '')),
            'skills':          request.form.get('skills', ''),
            'experience':      request.form.get('experience', ''),
            'education':       request.form.get('education', ''),
            'job_preferences': request.form.get('job_preferences', ''),
            'profile':         request.form.get('profile', ''),
            'projects':        request.form.get('projects', ''),
            'image_path':      resume_data.get('image_path', DEFAULT_PROFILE_PIC.replace('static/', '')),
            'dynamic_sections': resume_data.get('dynamic_sections', {}),
        }

        session['final_resume_filename'] = save_data_to_file(updated, 'resume_final')
        return redirect(url_for('resume'))

    return render_template('handler.html', resume_data=resume_data, ai_sections=ai_sections)


@app.route('/resume')
def resume():
    filename = session.get('final_resume_filename', session.get('resume_filename'))
    if not filename:
        flash('Please fill out the form first.')
        return redirect(url_for('form'))

    resume_data = load_data_from_file(filename)
    if not resume_data:
        flash('Error loading your resume data. Please try again.')
        return redirect(url_for('form'))

    # Ensure all expected keys exist (guard against older sessions)
    defaults = {
        'name': '', 'email': '', 'phone': '', 'links': '',
        'skills': '', 'experience': '', 'education': '',
        'job_preferences': '', 'profile': '', 'projects': '',
        'image_path': DEFAULT_PROFILE_PIC.replace('static/', ''),
        'dynamic_sections': {},
    }
    for k, v in defaults.items():
        resume_data.setdefault(k, v)

    return render_template('resume.html', resume_data=resume_data)


@app.route('/download_pdf', methods=['POST'])
def download_pdf():
    """Generate and download a PDF using WeasyPrint."""
    try:
        from weasyprint import HTML
    except ImportError:
        flash('WeasyPrint is not installed. Please run: pip install weasyprint')
        return redirect(url_for('resume'))

    filename = session.get('final_resume_filename', session.get('resume_filename'))
    resume_data = load_data_from_file(filename) if filename else None

    if not resume_data:
        flash('No resume data found.')
        return redirect(url_for('form'))

    defaults = {
        'name': '', 'email': '', 'phone': '', 'links': '',
        'skills': '', 'experience': '', 'education': '',
        'job_preferences': '', 'profile': '', 'projects': '',
        'image_path': DEFAULT_PROFILE_PIC.replace('static/', ''),
        'dynamic_sections': {},
    }
    for k, v in defaults.items():
        resume_data.setdefault(k, v)

    # Build absolute photo URL for WeasyPrint
    root_dir = os.path.abspath(os.path.dirname(__file__))
    photo_url = None
    if resume_data.get('image_path'):
        photo_url = f"file:///{os.path.join(root_dir, 'static', resume_data['image_path']).replace(os.sep, '/')}"

    rendered_html = render_template('pdf_template.html', resume_data=resume_data, photo_url=photo_url)
    base_url = f"file:///{root_dir.replace(os.sep, '/')}"
    pdf_bytes = HTML(string=rendered_html, base_url=base_url).write_pdf()

    safe_name = resume_data.get('name', 'resume').replace(' ', '_').lower()
    return send_file(
        io.BytesIO(pdf_bytes),
        mimetype='application/pdf',
        download_name=f"{safe_name}_resume.pdf",
        as_attachment=True
    )


# ── AI Content Generation ──────────────────────────────────────────────────────
def _safe_generate(prompt, fallback):
    """Call Gemini safely with timeout; return fallback text on any error."""
    try:
        resp = model.generate_content(
            prompt,
            request_options={"timeout": REQUEST_TIMEOUT}
        )
        return resp.text.strip()
    except Exception as e:
        app.logger.error(f"Gemini API error: {e}")
        return fallback



def generate_ai_content(name, skills, experience, education, job_preferences,
                        projects='', profile=None):
    """Generate AI-enhanced resume content using Gemini."""
    ai_sections = {}

    # Professional profile
    if not profile or not profile.strip():
        prompt = f"""Write a concise, professional resume summary (3-5 sentences) for {name}.
Skills: {skills}
Experience: {experience}
Education: {education}
Job Goal: {job_preferences}
Return ONLY the summary text, no headings."""
        ai_sections['profile'] = {
            'content': _safe_generate(prompt, f"Experienced professional with expertise in {skills}."),
            'suggestions': "Personalize with specific achievements and career milestones."
        }

    # Skills
    prompt = f"""You are a professional resume writer. Reorganize and enhance this skills section into clear categories (Technical, Soft Skills, Tools, etc.) with bullet points.
Skills: {skills}
Return ONLY the formatted skills list, no extra commentary."""
    ai_sections['skills'] = {
        'content': _safe_generate(prompt, skills),
        'suggestions': "Prioritize skills most relevant to your target role."
    }

    # Experience
    prompt = f"""You are a professional resume writer. Rewrite each job entry below using strong action verbs and quantifiable achievements. Format as: Company | Title | Dates followed by 3-5 bullet points starting with action verbs.
Experience: {experience}
Return ONLY the formatted experience, no extra commentary."""
    ai_sections['experience'] = {
        'content': _safe_generate(prompt, experience),
        'suggestions': "Add numbers and metrics where possible (e.g., 'Reduced load time by 40%')."
    }

    # Education
    prompt = f"""Format this education information professionally for a resume. Include institution, degree, major, graduation year, and any notable achievements.
Education: {education}
Return ONLY the formatted education, no extra commentary."""
    ai_sections['education'] = {
        'content': _safe_generate(prompt, education),
        'suggestions': "Include GPA (if 3.5+), relevant coursework, or academic honors."
    }

    # Job preferences / Career objective
    prompt = f"""Convert these job preferences into a single, targeted career objective statement (1-2 sentences) for a resume.
Preferences: {job_preferences}
Return ONLY the objective statement."""
    ai_sections['job_preferences'] = {
        'content': _safe_generate(prompt, job_preferences),
        'suggestions': "Keep your objective specific and tailored to the role you want."
    }

    # Projects (if provided)
    if projects and projects.strip():
        prompt = f"""You are a professional resume writer. Reformat these projects for a resume. For each project, bold the name, then include 2-3 bullet points describing technologies used, your role, and the outcome.
Projects: {projects}
Return ONLY the formatted projects."""
        ai_sections['projects'] = {
            'content': _safe_generate(prompt, projects),
            'suggestions': "Link to GitHub or live demos if available."
        }

    return ai_sections


@app.route('/regenerate', methods=['POST'])
def regenerate():
    """AJAX: regenerate AI content for a single resume section from updated user input."""
    data = request.get_json(silent=True) or {}
    key     = data.get('key', '').strip()
    content = data.get('content', '').strip()
    name    = data.get('name', 'the candidate').strip()

    if not key or not content:
        return jsonify({'error': 'Missing key or content'}), 400

    section_prompts = {
        'profile': (
            f"Write a concise professional resume summary (3-5 sentences) for {name}. "
            f"Base it on: {content}. "
            f"Return ONLY the summary text, no headings, no markdown."
        ),
        'skills': (
            f"Reorganize and enhance these skills into clear categories (Technical, Soft Skills, Tools) "
            f"using plain text with bullet points (•). Skills: {content}. "
            f"Return ONLY the formatted list, no markdown, no extra commentary."
        ),
        'experience': (
            f"Rewrite each job entry using strong action verbs and quantifiable achievements. "
            f"Format: first line = Company | Title | Dates, then bullet points (•) for responsibilities. "
            f"Experience: {content}. Return ONLY plain text, no markdown."
        ),
        'projects': (
            f"Reformat these projects for a resume. First line of each = project name (plain, no asterisks). "
            f"Then 2-3 bullet points (•) describing tech, role, and outcome. "
            f"Projects: {content}. Return ONLY plain text, no markdown."
        ),
        'education': (
            f"Format this education for a resume. First line = Institution | Degree | Year, "
            f"then relevant details on next lines. Education: {content}. "
            f"Return ONLY plain text, no markdown."
        ),
        'job_preferences': (
            f"Convert to a concise 1-2 sentence career objective. Preferences: {content}. "
            f"Return ONLY the objective, no markdown."
        ),
    }

    prompt = section_prompts.get(key)
    if not prompt:
        return jsonify({'error': f'Unknown section: {key}'}), 400

    enhanced = _safe_generate(prompt, content)
    return jsonify({'content': enhanced})


if __name__ == '__main__':
    app.run(debug=True)
