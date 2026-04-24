from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Initialize Flask app
app = Flask(__name__)

# Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///notes.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Initialize database
db = SQLAlchemy(app)

# Database Model
class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Note {self.id}: {self.title}>'

# Create database tables
with app.app_context():
    db.create_all()

# Routes
@app.route('/', methods=['GET', 'POST'])
def index():
    """Display all notes and handle creating new notes"""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        # Validation
        if not title:
            flash('Title cannot be empty', 'error')
            return redirect(url_for('index'))

        if not content:
            flash('Content cannot be empty', 'error')
            return redirect(url_for('index'))

        # Create new note
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

    # Get all notes, ordered by creation date (newest first)
    notes = Note.query.order_by(Note.created_at.desc()).all()
    return render_template('index.html', notes=notes)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    """Edit an existing note"""
    note = Note.query.get_or_404(id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()

        # Validation
        if not title:
            flash('Title cannot be empty', 'error')
            return redirect(url_for('edit', id=id))

        if not content:
            flash('Content cannot be empty', 'error')
            return redirect(url_for('edit', id=id))

        # Update note
        try:
            note.title = title
            note.content = content
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
    """Delete a note"""
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
