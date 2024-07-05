from contextlib import contextmanager
from datetime import datetime

from celery import shared_task
from celery.utils.log import get_task_logger
from django_celery_results.models import TaskResult

from api.ai.analyzer.asset_analyzer import AssetAnalyzer
from api.ai.analyzer.note_analyzer import ExistingNoteAnalyzer, NewNoteAnalyzer
from api.ai.analyzer.project_summarizer import ProjectSummarizer
from api.mixpanel import mixpanel
from api.models.asset import Asset
from api.models.integrations.slack.slack_message_buffer import SlackMessageBuffer
from api.models.note import Note
from api.models.project import Project
from api.models.takeaway_type import TakeawayType
from api.models.user import User

logger = get_task_logger(__name__)


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
def analyze_existing_note(note_id, takeaway_type_ids, user_id):
    print(
        f"analyzing existing note {note_id} with takeaway types {takeaway_type_ids} by {user_id}"
    )

    note = Note.objects.select_related("project__workspace").get(id=note_id)
    if note.is_analyzing:
        return

    takeaway_types = note.project.takeaway_types.filter(id__in=takeaway_type_ids)
    if not takeaway_types:
        return

    user = User.objects.get(id=user_id)
    with is_analyzing(note):
        analyzer = ExistingNoteAnalyzer()
        analyzer.analyze(note, takeaway_types, user)


@shared_task(bind=True, track_started=True)
def analyze_asset(self, project_id, note_ids, takeaway_type_ids, user_id):
    print(
        f"analyzing asset with {note_ids} and takeaway types {takeaway_type_ids} by {user_id}"
    )
    project = Project.objects.get(id=project_id)
    user = User.objects.get(id=user_id)
    notes = Note.objects.filter(id__in=note_ids)
    takeaway_types = TakeawayType.objects.filter(id__in=takeaway_type_ids)

    # Create Asset
    task = TaskResult.objects.get(task_id=self.request.id)
    asset = Asset.objects.create(project=project, created_by=user, task=task)
    notes = notes.filter(project=asset.project)
    asset.notes.set(notes)
    mixpanel.track(
        user.id,
        "BE: Asset Created",
        {
            "asset_id": asset.id,
            "project_id": asset.project.id,
            "created_manually": False,
        },
    )

    # Generate for each takeaway type
    bot = User.objects.get(username="bot@raijin.ai")
    for i, note in enumerate(notes):
        note_takeaway_types = takeaway_types.exclude(
            takeaways__note=note, takeaways__created_by=bot
        )
        self.update_state(
            state="PROGRESS",
            meta={"step": "analyzing report", "current": i + 1, "total": len(notes)},
        )
        with is_analyzing(note):
            analyzer = ExistingNoteAnalyzer()
            analyzer.analyze(note, note_takeaway_types, user)

        # Generate asset
        self.update_state(
            state="PROGRESS",
            meta={"step": "generating asset"},
        )
    analyzer = AssetAnalyzer()
    analyzer.analyze(asset, takeaway_types, user)


@shared_task
def process_slack_messages():
    try:
        current_time = datetime.now()
        # logger.info("Starting to process slack messages")
        messages = SlackMessageBuffer.objects.all()
        # print(f"process slack messages task executed at time: {current_time}")
        for msg in messages:
            notes = Note.objects.filter(
                slack_channel_id=msg.slack_channel_id, slack_team_id=msg.slack_team_id
            )
            for note in notes:
                # If note.content is empty or doesn't have the "root" structure, add it
                if not note.content or "root" not in note.content:
                    note.content = {
                        "root": {
                            "type": "root",
                            "format": "",
                            "version": 1,
                            "children": [],
                            "direction": "ltr",
                        }
                    }

                root_children = note.content["root"]["children"]

                new_message_paragraph = {
                    "type": "paragraph",
                    "format": "",
                    "version": 1,
                    "children": [
                        {
                            "mode": "normal",
                            "text": f"*{msg.slack_user}:* {msg.message_text} (_{msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}_)",
                            "type": "text",
                            "style": "",
                            "detail": 0,
                            "format": 0,
                            "version": 1,
                        }
                    ],
                    "direction": "ltr",
                }

                root_children.append(new_message_paragraph)
                note.content["root"]["children"] = root_children
                note.save()

        # After processing, clear buffer
        messages.delete()

    except Exception as e:
        logger.exception("Failed to process slack messages: %s", str(e))
