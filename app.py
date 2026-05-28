from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import pytz
IST = pytz.timezone('Asia/Kolkata')

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

db = SQLAlchemy(app)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    
    def get_ist_time():
        return datetime.now(IST).replace(tzinfo=None)
    
    created_at = db.Column(db.DateTime, default=get_ist_time)
    updated_at = db.Column(db.DateTime, default=get_ist_time, onupdate=get_ist_time)
    
    def __repr__(self):
        return f'<Note {self.id}: {self.title}>'

with app.app_context():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not title:
            flash('Title cannot be empty', 'error')
            return redirect(url_for('index'))

        if not content:
            flash('Content cannot be empty', 'error')
            return redirect(url_for('index'))

        if len(content) > 1000:
            flash('Content cannot exceed 1000 characters.', 'error')
            return redirect(url_for('index'))

        try:
            note = Note(title=title, content=content)
            db.session.add(note)
            db.session.commit()
            flash('Note created successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error creating note. Please try again.', 'error')
            return redirect(url_for('index'))

    query = request.args.get('q', '').strip()
    if query:
        notes = Note.query.filter(
            Note.title.ilike(f'%{query}%') | Note.content.ilike(f'%{query}%')
        ).order_by(Note.created_at.desc()).all()
    else:
        notes = Note.query.order_by(Note.created_at.desc()).all()

    return render_template('index.html', notes=notes, query=query)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    note = Note.query.get_or_404(id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        if not title:
            flash('Title cannot be empty', 'error')
            return redirect(url_for('edit', id=id))

        if not content:
            flash('Content cannot be empty', 'error')
            return redirect(url_for('edit', id=id))
        
        if len(content) > 1000:
            flash('Content cannot exceed 1000 characters.', 'error')
            return redirect(url_for('index'))

        try:
            note.title = title
            note.content = content
            note.updated_at = datetime.now(IST).replace(tzinfo=None)
            db.session.commit()
            flash('Note updated successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash('Error updating note. Please try again.', 'error')
            return redirect(url_for('edit', id=id))

    return render_template('edit.html', note=note)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    note = Note.query.get_or_404(id)

    try:
        db.session.delete(note)
        db.session.commit()
        flash('Note deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting note. Please try again.', 'error')

    return redirect(url_for('index'))

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def server_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
