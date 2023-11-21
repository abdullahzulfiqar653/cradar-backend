from django.contrib.auth.models import User
from django.db import models
from shortuuid.django_fields import ShortUUIDField

from project.models import Project
from tag.models import Tag


class Takeaway(models.Model):
    class Status(models.TextChoices):
        OPEN = "Open"
        ONHOLD = "Onhold"
        CLOSE = "Closed"

    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.TextField()
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name="takeaways")
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_takeaways",
        related_query_name="created_takeaways",
    )
    upvoted_by = models.ManyToManyField(
        User, related_name="upvoted_takeaways", related_query_name="upvoted_takeaways"
    )
    status = models.CharField(max_length=6, choices=Status.choices, default=Status.OPEN)
    note = models.ForeignKey(
        "note.Note", on_delete=models.CASCADE, related_name="takeaways"
    )
    code = models.CharField(max_length=10, unique=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.code == "":
            self.code = f"{self.note.code}-{self.note.takeaway_sequence + 1}"
            note = self.note
            note.takeaway_sequence += 1
            note.save()
        super().save(*args, **kwargs)


class Highlight(Takeaway):
    start = models.IntegerField()
    end = models.IntegerField()

    def save(self, *args, **kwargs):
        content = " ".join(self.note.content.split(" "))
        self.title = content[self.start : self.end]
        return super().save(*args, **kwargs)


class Insight(models.Model):
    id = ShortUUIDField(length=12, max_length=12, primary_key=True, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField()
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="insights"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="insights"
    )
    takeaways = models.ManyToManyField(Takeaway, related_name="insights")
