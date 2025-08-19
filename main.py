from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from routes.quizassign import (quizzes, assignments, evaluation, submission, generate_questions, explain_answers)
from routes.quizassign.assignment_fetch import router as assignment_fetch_router
from routes.quizassign.faculty_view import router as Faculty_router
from routes.quizassign.student_view import router as Student_router
from routes.auth.auth import router as auth_router
from routes.auth.face_login import router as face_login_router
from routes.chatbot.chat import router as chat_router
from difflib import SequenceMatcher
from flask_login import LoginManager
from routes.auth.user import DummyUser
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

login_manager = LoginManager()
login_manager.init_app(app)

app.secret_key = os.getenv("SECRET_KEY", "supersecretkey123")

# Register blueprints from all routes
app.register_blueprint(evaluation.router)
app.register_blueprint(quizzes.router)
app.register_blueprint(assignments.router)
app.register_blueprint(submission.router)
app.register_blueprint(assignment_fetch_router)
app.register_blueprint(Faculty_router)
app.register_blueprint(Student_router)
app.register_blueprint(generate_questions.router)
app.register_blueprint(explain_answers.router)
app.register_blueprint(auth_router)
app.register_blueprint(face_login_router)
app.register_blueprint(chat_router)

@app.route("/", methods=["GET"])
def root():
    return jsonify({"msg": "Backend is running"})

@login_manager.user_loader
def load_user(user_id):
    return DummyUser(user_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
