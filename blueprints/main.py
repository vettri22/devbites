from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, abort
from flask_login import login_required, current_user
from extensions import db, csrf
from models import Bite, Category, Progress, QuizQuestion, QuizAttempt, User, XPLog
from recommend import recommend_bites
from config import Config

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    categories = Category.query.all()
    total_bites = Bite.query.count()
    total_users = User.query.count()
    featured = Bite.query.order_by(Bite.order_index.asc()).limit(6).all()
    return render_template(
        "index.html",
        categories=categories,
        total_bites=total_bites,
        total_users=total_users,
        featured=featured,
    )


@main_bp.route("/dashboard")
@login_required
def dashboard():
    completed_ids = current_user.completed_bite_ids()
    recommendations = recommend_bites(current_user, limit=4, completed_ids=completed_ids)
    recent_attempts = (
        QuizAttempt.query.filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.attempted_at.desc())
        .limit(5)
        .all()
    )
    total_bites = Bite.query.count()
    progress_pct = round((len(completed_ids) / total_bites) * 100) if total_bites else 0

    return render_template(
        "dashboard.html",
        completed_count=len(completed_ids),
        total_bites=total_bites,
        progress_pct=progress_pct,
        recommendations=recommendations,
        recent_attempts=recent_attempts,
    )


@main_bp.route("/bites")
def bites_list():
    page = request.args.get("page", 1, type=int)
    category_slug = request.args.get("category")
    difficulty = request.args.get("difficulty")
    search = request.args.get("q", "").strip()

    query = Bite.query
    if category_slug:
        cat = Category.query.filter_by(slug=category_slug).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
    if difficulty:
        query = query.filter_by(difficulty=difficulty)
    if search:
        query = query.filter(Bite.title.ilike(f"%{search}%"))

    pagination = query.order_by(Bite.order_index.asc()).paginate(
        page=page, per_page=Config.BITES_PER_PAGE, error_out=False
    )
    categories = Category.query.all()
    completed_ids = current_user.completed_bite_ids() if current_user.is_authenticated else []

    return render_template(
        "bites_list.html",
        pagination=pagination,
        bites=pagination.items,
        categories=categories,
        completed_ids=completed_ids,
        active_category=category_slug,
        active_difficulty=difficulty,
        search=search,
    )


@main_bp.route("/bites/<slug>")
def bite_detail(slug):
    bite = Bite.query.filter_by(slug=slug).first_or_404()

    if bite.is_premium and current_user.is_authenticated and current_user.plan == "free":
        flash("This bite is part of our Premium track. Please upgrade your plan.", "warning")
        return redirect(url_for("payment.pricing"))
    if bite.is_premium and not current_user.is_authenticated:
        flash("Please log in to access premium content.", "warning")
        return redirect(url_for("auth.login"))

    questions = bite.quiz_questions.all()
    is_completed = False
    if current_user.is_authenticated:
        progress = Progress.query.filter_by(user_id=current_user.id, bite_id=bite.id).first()
        is_completed = bool(progress and progress.completed)

    related = (
        Bite.query.filter(Bite.category_id == bite.category_id, Bite.id != bite.id)
        .limit(3)
        .all()
    )

    return render_template(
        "bite_detail.html", bite=bite, questions=questions, is_completed=is_completed, related=related
    )


@main_bp.route("/bites/<int:bite_id>/complete", methods=["POST"])
@csrf.exempt
@login_required
def complete_bite(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    progress = Progress.query.filter_by(user_id=current_user.id, bite_id=bite.id).first()

    if not progress:
        progress = Progress(user_id=current_user.id, bite_id=bite.id)
        db.session.add(progress)

    newly_completed = not progress.completed
    progress.completed = True
    progress.completed_at = datetime.utcnow()

    if newly_completed:
        current_user.xp += Config.XP_PER_BITE
        current_user.update_streak()
        db.session.add(XPLog(user_id=current_user.id, amount=Config.XP_PER_BITE, reason="bite_complete"))

    db.session.commit()
    return jsonify(
        {
            "success": True,
            "xp": current_user.xp,
            "level": current_user.level(),
            "streak": current_user.streak_count,
        }
    )


@main_bp.route("/bites/<int:bite_id>/uncomplete", methods=["POST"])
@csrf.exempt
@login_required
def uncomplete_bite(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    progress = Progress.query.filter_by(user_id=current_user.id, bite_id=bite.id).first()

    if progress and progress.completed:
        progress.completed = False
        progress.completed_at = None
        db.session.commit()

    return jsonify({"success": True})


@main_bp.route("/bites/<int:bite_id>/quiz", methods=["POST"])
@csrf.exempt
@login_required
def submit_quiz(bite_id):
    bite = Bite.query.get_or_404(bite_id)
    questions = bite.quiz_questions.all()
    data = request.get_json() or {}
    answers = data.get("answers", {})

    is_first_attempt = (
        QuizAttempt.query.filter_by(user_id=current_user.id, bite_id=bite.id).first() is None
    )

    score = 0
    results = []
    for q in questions:
        selected = answers.get(str(q.id))
        correct = selected == q.correct_option
        if correct:
            score += 1
            if is_first_attempt:
                current_user.xp += Config.XP_PER_QUIZ_CORRECT
                db.session.add(
                    XPLog(user_id=current_user.id, amount=Config.XP_PER_QUIZ_CORRECT, reason="quiz_correct")
                )
        results.append(
            {
                "question_id": q.id,
                "correct": correct,
                "correct_option": q.correct_option,
                "explanation": q.explanation,
            }
        )

    attempt = QuizAttempt(
        user_id=current_user.id, bite_id=bite.id, score=score, total_questions=len(questions)
    )
    db.session.add(attempt)
    db.session.commit()

    return jsonify(
        {
            "success": True,
            "score": score,
            "total": len(questions),
            "xp": current_user.xp,
            "xp_awarded": is_first_attempt,
            "results": results,
        }
    )


@main_bp.route("/profile")
@login_required
def profile():
    completed_ids = current_user.completed_bite_ids()
    attempts = QuizAttempt.query.filter_by(user_id=current_user.id).all()
    avg_score = 0
    if attempts:
        avg_score = round(
            sum(a.score / a.total_questions for a in attempts if a.total_questions) / len(attempts) * 100
        )
    return render_template(
        "profile.html",
        completed_count=len(completed_ids),
        attempts_count=len(attempts),
        avg_score=avg_score,
        certificates=current_user.certificates.all(),
    )


@main_bp.route("/leaderboard")
def leaderboard():
    top_users = User.query.order_by(User.xp.desc()).limit(20).all()
    return render_template("leaderboard.html", top_users=top_users)
