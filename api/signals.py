from django.db.models import Count
from django.db.models.signals import m2m_changed, post_delete
from django.dispatch import receiver

from api.models.keyword import Keyword
from api.models.note import Note
from api.models.note_template import NoteTemplate
from api.models.note_template_type import NoteTemplateType
from api.models.organization import Organization
from api.models.question import Question
from api.models.tag import Tag
from api.models.takeaway import Takeaway
from api.models.takeaway_type import TakeawayType


def cleanup_keywords():
    Keyword.objects.annotate(note_count=Count("notes")).filter(note_count=0).delete()


def cleanup_organizations():
    Organization.objects.annotate(note_count=Count("notes")).filter(
        note_count=0
    ).delete()


def cleanup_tags():
    Tag.objects.filter(takeaway_count=0).delete()


def cleanup_takeaway_types():
    TakeawayType.objects.annotate(takeaway_count=Count("takeaways")).filter(
        takeaway_count=0
    ).delete()


def cleanup_note_template_types():
    NoteTemplateType.objects.annotate(
        note_template_count=Count("note_templates")
    ).filter(note_template_count=0).delete()


def cleanup_questions():
    Question.objects.annotate(note_template_count=Count("note_templates")).filter(
        note_template_count=0
    ).delete()


@receiver(m2m_changed, sender=Note.keywords.through)
def note_keywords_changed(sender, action, instance, reverse, pk_set, **kwargs):
    if action in ("post_remove", "post_clear"):
        cleanup_keywords()


@receiver(post_delete, sender=Note)
def post_delete_note(sender, instance, **kwargs):
    cleanup_keywords()
    cleanup_organizations()


@receiver(m2m_changed, sender=Takeaway.tags.through)
def takeaway_tags_changed(sender, action, instance, reverse, pk_set, **kwargs):
    if action in ("post_remove", "post_clear"):
        cleanup_tags()


@receiver(post_delete, sender=Takeaway)
def post_delete_takeaway(sender, instance, **kwargs):
    cleanup_tags()
    cleanup_takeaway_types()


@receiver(m2m_changed, sender=NoteTemplate.questions.through)
def note_template_questions_changed(
    sender, action, instance, reverse, pk_set, **kwargs
):
    if action in ("post_remove", "post_clear"):
        cleanup_questions()


@receiver(post_delete, sender=NoteTemplate)
def post_delete_note_template(sender, instance, **kwargs):
    cleanup_questions()
    cleanup_note_template_types()
