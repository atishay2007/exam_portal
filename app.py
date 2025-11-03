from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import json, random, os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import timedelta

app = Flask(__name__)
app.secret_key = 'vit_exam_secret_2025'
app.permanent_session_lifetime = timedelta(minutes=60)

DATA_USERS = 'users.json'
DATA_Q = 'questions.json'
DATA_LEADER = 'leaderboard.json'
ADMIN_USER = 'admin'
ADMIN_PASS = 'admin123'  # change before final submission

# ---------- Helpers ----------
def read_json(path):
    if not os.path.exists(path):
        # create default structures
        if path == DATA_USERS:
            with open(path, 'w') as f:
                json.dump({}, f)
        else:
            with open(path, 'w') as f:
                json.dump([], f)
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            # if file is empty or corrupted, reset sensible default
            if path == DATA_USERS:
                return {}
            return []

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def ensure_question_ids(path=DATA_Q):
    """
    Ensure every question has an integer 'id'; assign one where missing.
    Returns the list of question dicts.
    """
    data = read_json(path)
    changed = False
    if not isinstance(data, list):
        # if questions.json has wrong format, reset to empty list
        data = []
        changed = True
    for q in data:
        if not isinstance(q, dict):
            continue
        if 'id' not in q:
            q['id'] = random.randint(100000, 999999)
            changed = True
    if changed:
        write_json(path, data)
    return data

def find_question_by_id(qid):
    all_q = ensure_question_ids()
    return next((q for q in all_q if int(q.get('id', 0)) == int(qid)), None)

# ---------- Routes ----------
@app.route('/')
def home():
    leader = read_json(DATA_LEADER) if os.path.exists(DATA_LEADER) else []
    return render_template('index.html', leaderboard=leader[:5])

@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        try:
            users = read_json(DATA_USERS)
            uname = request.form['username'].strip()
            pwd = request.form['password']
            name = request.form['name']
            reg = request.form['reg']
            course = request.form['course']
            year = request.form['year']
            dept = request.form['dept']
        except KeyError as e:
            flash(f"Missing field: {e}", "danger")
            return redirect(url_for('signup'))

        if not uname or uname in users:
            flash('Username invalid or taken', 'danger')
            return redirect(url_for('signup'))

        users[uname] = {
            'password': generate_password_hash(pwd),
            'scores': [],
            'name': name,
            'reg': reg,
            'course': course,
            'year': year,
            'dept': dept
        }
        write_json(DATA_USERS, users)
        flash('Account created. Please login.', 'success')
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        users = read_json(DATA_USERS)
        uname = request.form['username'].strip()
        pwd = request.form['password']
        if uname in users and check_password_hash(users[uname]['password'], pwd):
            session.permanent = True
            session['user'] = uname
            flash('Logged in successfully', 'success')
            return redirect(url_for('profile'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('home'))

# Profile
@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    users = read_json(DATA_USERS)
    uname = session['user']
    user = users.get(uname, {})
    scores = user.get('scores', [])
    return render_template('profile.html', username=uname, user=user, scores=scores)

# Quiz start: choose difficulty, number, per-question time
@app.route('/quiz_start', methods=['GET','POST'])
def quiz_start():
    if 'user' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        difficulty = request.form.get('difficulty')
        try:
            count = int(request.form.get('count', 5))
        except ValueError:
            count = 5
        try:
            per_q = int(request.form.get('per_q', 30))
        except ValueError:
            per_q = 30
        all_q = ensure_question_ids(DATA_Q)
        pool = [q for q in all_q if difficulty == 'any' or q.get('difficulty') == difficulty]
        random.shuffle(pool)
        selected = pool[:max(1, min(len(pool), count))]
        # store minimal necessary data in session (do not include large items)
        session['quiz'] = {
            'questions': selected,
            'answers': [],
            'current': 0,
            'per_q': per_q
        }
        return redirect(url_for('quiz'))
    all_q = ensure_question_ids(DATA_Q)
    diffs = sorted(list({q.get('difficulty','unspecified') for q in all_q}))
    return render_template('quiz_start.html', difficulties=diffs)

# Serve quiz page (one question at a time)
@app.route('/quiz', methods=['GET','POST'])
def quiz():
    if 'user' not in session or 'quiz' not in session:
        return redirect(url_for('quiz_start'))
    quiz_data = session['quiz']
    qlist = quiz_data['questions']
    idx = quiz_data['current']
    if request.method == 'POST':
        ans = request.form.get('option','')
        quiz_data['answers'].append(ans)
        quiz_data['current'] += 1
        session['quiz'] = quiz_data
        if quiz_data['current'] >= len(qlist):
            return redirect(url_for('result'))
        return redirect(url_for('quiz'))
    # GET
    if idx >= len(qlist):
        return redirect(url_for('result'))
    question = qlist[idx]
    progress = int((idx / len(qlist)) * 100)
    return render_template('quiz.html', q=question, idx=idx, total=len(qlist), progress=progress, per_q=quiz_data['per_q'])

# Result and review store scores
@app.route('/result')
def result():
    if 'user' not in session or 'quiz' not in session:
        return redirect(url_for('home'))
    quiz = session.pop('quiz')
    qlist = quiz['questions']
    answers = quiz['answers']
    score = 0
    review = []
    for i, q in enumerate(qlist):
        user_ans = answers[i] if i < len(answers) else ''
        correct = q.get('answer','')
        ok = (user_ans == correct)
        if ok:
            score += 1
        review.append({'question': q['question'], 'options': q.get('options', []), 'your': user_ans, 'correct': correct, 'ok': ok})
    # store in users.json and leaderboard.json
    users = read_json(DATA_USERS)
    uname = session.get('user')
    if uname and uname in users:
        users[uname].setdefault('scores', []).append({'score':score, 'out_of': len(qlist)})
        write_json(DATA_USERS, users)
    leader = read_json(DATA_LEADER) if os.path.exists(DATA_LEADER) else []
    leader.append({'user': uname, 'score': score, 'out_of': len(qlist)})
    leader = sorted(leader, key=lambda x: x['score'], reverse=True)
    write_json(DATA_LEADER, leader)
    return render_template('result.html', score=score, out_of=len(qlist), review=review)

# ---------- Admin: login + CRUD ----------
@app.route('/admin', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        u = request.form.get('username')
        p = request.form.get('password')
        if u == ADMIN_USER and p == ADMIN_PASS:
            session['admin'] = True
            flash('Admin logged in', 'success')
            return redirect(url_for('admin_panel'))
        flash('Admin login failed', 'danger')
    return render_template('admin_login.html')

@app.route('/admin_panel')
def admin_panel():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    all_q = ensure_question_ids(DATA_Q)
    return render_template('admin.html', questions=all_q)

@app.route('/admin_add', methods=['POST'])
def admin_add():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    data = ensure_question_ids(DATA_Q)
    # create new question dict
    new = {
        'id': random.randint(100000,999999),
        'question': request.form.get('question', '').strip(),
        'options': [
            request.form.get('opt1', '').strip(),
            request.form.get('opt2', '').strip(),
            request.form.get('opt3', '').strip(),
            request.form.get('opt4', '').strip()
        ],
        'answer': request.form.get('answer', '').strip(),
        'difficulty': request.form.get('difficulty','easy')
    }
    data.append(new)
    write_json(DATA_Q, data)
    flash('Question added', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin_delete/<int:qid>')
def admin_delete(qid):
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    data = ensure_question_ids(DATA_Q)
    data = [q for q in data if int(q.get('id', 0)) != int(qid)]
    write_json(DATA_Q, data)
    flash('Deleted', 'info')
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit/<qid>', methods=['GET', 'POST'])

def edit_question(qid):
    questions = ensure_question_ids(DATA_Q)
    q = next((q for q in questions if q['id'] == qid), None)
    if not q:
        flash('Question not found', 'danger')
        return redirect(url_for('admin_panel'))

    if request.method == 'POST':
        q['question'] = request.form['question']
        q['options'] = [
            request.form['opt1'],
            request.form['opt2'],
            request.form['opt3'],
            request.form['opt4']
        ]
        q['answer'] = request.form['answer']
        q['difficulty'] = request.form['difficulty']
        write_json(DATA_Q, questions)
        flash('Question updated.', 'success')
        return redirect(url_for('admin_panel'))

    return render_template('edit_question.html', q=q)


# Simple leaderboard API
@app.route('/leaderboard')
def leaderboard():
    leader = read_json(DATA_LEADER) if os.path.exists(DATA_LEADER) else []
    return jsonify(leader[:10])

@app.route('/recover', methods=['GET', 'POST'])
def recover():
    if request.method == 'POST':
        uname = request.form['username'].strip()
        users = read_json(DATA_USERS)
        if uname not in users:
            flash('Username not found', 'danger')
            return redirect(url_for('recover'))
        # Update password
        new_pwd = request.form['new_password']
        users[uname]['password'] = generate_password_hash(new_pwd)
        write_json(DATA_USERS, users)
        flash('Password updated. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('recover.html')


@app.route('/questions')
def view_questions():
    all_q = ensure_question_ids(DATA_Q)
    return render_template('questions.html', questions=all_q)

if __name__ == '__main__':
    # ensure question ids exist at startup
    ensure_question_ids(DATA_Q)
    app.run(debug=True)
