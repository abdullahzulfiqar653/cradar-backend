from celery import shared_task
from django.utils import translation

from api.ai.analyzer.note_analyzer import ExistingNoteAnalyzer, NewNoteAnalyzer
from api.ai.analyzer.project_summarizer import ProjectSummarizer
from api.models.note import Note
from api.models.user import User


@shared_task
def summarize_projects():
    print("summarizing projects")
    bot = User.objects.get(username="bot@raijin.ai")
    project_summarizer = ProjectSummarizer()
    project_summarizer.summarize_all_projects(created_by=bot)


@shared_task
def analyze_new_note(note_id, user_id):
    print(f"analyzing new note {note_id} by {user_id}")
    analyzer = NewNoteAnalyzer()
    print("Debug: Done initializing analyzer")

    try:
        note = Note.objects.select_related("project__workspace").get(id=note_id)
    except Exception as e:
        print("Debug: Failed to connect to db")
        import traceback

        traceback.print_exc()
        raise e
    print("Debug: Done selecting the note")
    note.is_analyzing = True
    note.save()
    print("Debug: Done updating the note")

    user = User.objects.get(id=user_id)
    print("Debug: Done getting the user")

    with translation.override(note.project.language):
        print("Debug: Starting analyzer")
        analyzer.analyze(note, user)

    note.is_analyzing = False
    note.save()


@shared_task
def analyze_existing_note(note_id, user_id):
    print("analyzing existing note")
    analyzer = ExistingNoteAnalyzer()

    note = Note.objects.select_related("project__workspace").get(id=note_id)
    note.is_analyzing = True
    note.save()

    user = User.objects.get(id=user_id)

    with translation.override(note.project.language):
        analyzer.analyze(note, user)

    note.is_analyzing = False
    note.save()
