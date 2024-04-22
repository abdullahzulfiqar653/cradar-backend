import time
from contextlib import contextmanager

from celery import shared_task

from api.ai.analyzer.note_analyzer import (
    ExistingNoteAnalyzer,
    NewNoteAnalyzer,
    TranscribeOnlyAnalyzer,
)
from api.ai.analyzer.project_summarizer import ProjectSummarizer
from api.ai.generators.takeaway_generator_with_questions import (
    generate_takeaways_with_questions,
)
from api.models.note import Note
from api.models.user import User


@contextmanager
def is_analyzing(note: Note):
    try:
        note.is_analyzing = True
        note.save()
        yield None
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise e
    finally:
        note.is_analyzing = False
        note.save()


@shared_task
def summarize_projects():
    print("summarizing projects")
    bot = User.objects.get(username="bot@raijin.ai")
    project_summarizer = ProjectSummarizer()
    project_summarizer.summarize_all_projects(created_by=bot)


@shared_task
def analyze_new_note(note_id, user_id):
    print(f"analyzing new note {note_id} by {user_id}")
    # Wait for a moment for the db to save the new note
    time.sleep(1)
    try:
        note = Note.objects.select_related("project__workspace").get(id=note_id)
    except Exception as e:
        print("Debug: Failed to connect to db")
        import traceback

        from django.db import connection

        traceback.print_exc()
        print(connection.queries)
        raise e
    if note.is_analyzing:
        return

    user = User.objects.get(id=user_id)
    with is_analyzing(note):
        analyzer = NewNoteAnalyzer()
        analyzer.analyze(note, user)


@shared_task
def analyze_existing_note(note_id, user_id):
    print(f"analyzing existing note {note_id} by {user_id}")

    note = Note.objects.select_related("project__workspace").get(id=note_id)
    if note.is_analyzing:
        return

    user = User.objects.get(id=user_id)
    with is_analyzing(note):
        analyzer = ExistingNoteAnalyzer()
        analyzer.analyze(note, user)


@shared_task
def transcribe_note(note_id, user_id):
    print(f"analyzing existing note {note_id} by {user_id}")

    note = Note.objects.select_related("project__workspace").get(id=note_id)
    if note.is_analyzing:
        return

    user = User.objects.get(id=user_id)
    with is_analyzing(note):
        analyzer = TranscribeOnlyAnalyzer()
        analyzer.analyze(note, user)


@shared_task
def ask_note_question(note_id, question_id, user_id):
    note = Note.objects.select_related("project__workspace").get(id=note_id)
    if note.is_analyzing:
        return

    questions = note.questions.filter(id=question_id)
    user = User.objects.get(id=user_id)
    with is_analyzing(note):
        generate_takeaways_with_questions(note, questions, user)
