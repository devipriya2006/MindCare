        .order_by(MoodEntry.created_at.desc())
        .limit(5)
        .all()
    )

    total_entries = user_entries.count()

    week_ago = datetime.utcnow() - timedelta(days=7)

    week_entries = MoodEntry.query.filter(
        MoodEntry.user_id == current_user.id,
        MoodEntry.created_at >= week_ago,
    ).count()

    latest = recent_entries[0] if recent_entries else None

    return render_template(
        "dashboard.html",
        recent_entries=recent_entries,
        total_entries=total_entries,
        week_entries=week_entries,
        latest=latest,
    )


# --------------------------------------------------------------------------
# HISTORY
# --------------------------------------------------------------------------

@app.route("/history")
@login_required
def history():
    entries = (
        MoodEntry.query
        .filter_by(user_id=current_user.id)
        .order_by(MoodEntry.created_at.desc())
        .all()
    )

    return render_template("history.html", entries=entries)


# --------------------------------------------------------------------------
# SUPPORT / RESOURCES
# --------------------------------------------------------------------------

@app.route("/support")
def support():
    return render_template("support.html")


# --------------------------------------------------------------------------
# JSON API FOR DASHBOARD CHARTS
# --------------------------------------------------------------------------

@app.route("/api/mood-data")
@login_required
def mood_data():
    entries = (
        MoodEntry.query
        .filter_by(user_id=current_user.id)
        .order_by(MoodEntry.created_at.asc())
        .limit(30)
        .all()
    )

    trend = [
        {
            "date": (
                entry.created_at.strftime("%b %d")
                if entry.created_at else ""
            ),
            "score": entry.mood_score,
            "wellness_score": entry.wellness_score,
            "wellness_level": entry.wellness_level,
        }
        for entry in entries
    ]

    distribution = {
        "Positive": 0,
        "Neutral": 0,
        "Negative": 0,
    }

    for entry in entries:
        if entry.sentiment in distribution:
            distribution[entry.sentiment] += 1

    facial_distribution = {
        "angry": 0,
        "disgust": 0,
        "fear": 0,
        "happy": 0,
        "sad": 0,
        "surprise": 0,
        "neutral": 0,
    }
    for entry in entries:
        if entry.checkin_type == "automatic" and entry.confirmed_expression:
            if entry.confirmed_expression in facial_distribution:
                facial_distribution[entry.confirmed_expression] += 1

    return jsonify({
        "trend": trend,
        "distribution": distribution,
        "facial_distribution": facial_distribution,
    })


# --------------------------------------------------------------------------
# RUN APP
# --------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
