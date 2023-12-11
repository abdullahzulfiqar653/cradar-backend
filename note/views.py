import json
from decimal import Decimal
from pprint import pprint

from django.db.models import Count
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from langchain.callbacks import get_openai_callback
from langchain.chains.openai_functions import create_structured_output_chain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field, constr
from rest_framework import exceptions, generics, status
from rest_framework.response import Response
from tiktoken import encoding_for_model
from unidecode import unidecode

from note.models import Note
from note.serializers import NoteSerializer
from tag.models import Keyword, Tag
from tag.serializers import KeywordSerializer
from takeaway.models import Highlight, Takeaway
from takeaway.serializers import HighlightSerializer, TakeawaySerializer

encoder = encoding_for_model("gpt-3.5-turbo")


class TakeawaySchema(BaseModel):
    message: str = Field(description="message of the takeaway.")
    tags: list[constr(max_length=50)] = Field(
        description="Tags to be added to the takeaway."
    )


class TakeawayListSchema(BaseModel):
    takeaways: list[TakeawaySchema]


llm = ChatOpenAI()
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Given the following takeaway messages, add 3 - 5 tags to each takeaway message.",
        ),
        (
            "human",
            "{takeaways}",
        ),
    ]
)
chain = create_structured_output_chain(
    TakeawayListSchema.schema(), llm, prompt, verbose=True
)

# def attachment_create(request, note_id):
#     if request.method == 'POST':
#         form = AttachmentForm(request.POST, request.FILES)
#         if form.is_valid():
#             file = form.cleaned_data['file']
#             note = get_object_or_404(Note, id=note_id)
#             instance = form.save()
#             note.attachments.add(instance)

#             # # Upload to S3
#             # s3 = boto3.resource('s3')
#             # bucket_name = settings.AWS_STORAGE_BUCKET_NAME
#             # folder_name = 'note'
#             # file_key = f"{folder_name}/{file.name}"
#             # s3.Bucket(bucket_name).put_object(Key=file_key, Body=file)

#             return redirect('attachment-detail', note_id=note_id, attachment_id=instance.id)
#     else:
#         form = AttachmentForm()
#     return render(request, 'note_form.html', {'form': form})


class NoteRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Note.objects.all()
    serializer_class = NoteSerializer

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(takeaway_count=Count("takeaways"))
            .annotate(participant_count=Count("user_participants"))
        )

    def retrieve(self, request, pk):
        note = Note.objects.filter(id=pk).first()
        if note is None or not note.project.users.contains(request.user):
            raise exceptions.NotFound("Report not found.")
        return super().retrieve(request, pk)


class NoteTakeawayListCreateView(generics.ListCreateAPIView):
    queryset = Takeaway.objects.all()
    serializer_class = TakeawaySerializer
    ordering_fields = [
        "created_at",
        "created_by__first_name",
        "created_by__last_name",
        "title",
    ]
    ordering = ["created_at"]
    search_fields = [
        "title",
        "created_by__username",
        "created_by__first_name",
        "created_by__last_name",
    ]

    def get_queryset(self):
        auth_user = self.request.user
        note_id = self.kwargs.get("report_id")
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(auth_user):
            raise exceptions.PermissionDenied
        return Takeaway.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise exceptions.PermissionDenied
        request.data["note"] = note.id
        return super().create(request)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class NoteHighlightCreateView(generics.CreateAPIView):
    queryset = Highlight.objects.all()
    serializer_class = HighlightSerializer


class NoteKeywordListCreateView(generics.ListCreateAPIView):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer

    def get_queryset(self):
        auth_user = self.request.user
        note_id = self.kwargs.get("report_id")
        note = get_object_or_404(Note, id=note_id)
        if not note.project.users.contains(auth_user):
            raise exceptions.PermissionDenied
        return Keyword.objects.filter(note=note)

    def create(self, request, report_id):
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(request.user):
            raise exceptions.PermissionDenied
        request.data["note"] = note.id
        return super().create(request)

    def perform_create(self, serializer):
        report_id = self.kwargs.get("report_id")
        note = get_object_or_404(Note, id=report_id)
        if not note.project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        keyword = serializer.save()
        note.keywords.add(keyword)


class NoteKeywordDestroyView(generics.DestroyAPIView):
    serializer_class = KeywordSerializer

    def destroy(self, request, report_id, keyword_id):
        note = Note.objects.filter(pk=report_id, project__users=request.user).first()
        if note is None:
            raise exceptions.NotFound(f"Report {report_id} not found.")

        keyword = note.keywords.filter(pk=keyword_id).first()
        if keyword is None:
            raise exceptions.NotFound(f"Keyword {keyword_id} not found.")

        note.keywords.remove(keyword)
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(request=None, responses={200: None})
class NoteTagGenerateView(generics.CreateAPIView):
    def create(self, request, report_id):
        note = Note.objects.filter(id=report_id, project__users=request.user).first()
        if note is None:
            raise exceptions.NotFound("Report not found.")

        # Chunk takeaway list
        token_count = 0
        chunked_takeaway_lists = [[]]
        for takeaway in note.takeaways.all():
            token_count += len(encoder.encode(takeaway.title))
            if token_count < 1000:
                chunked_takeaway_lists[-1].append({"message": takeaway.title})
            else:  # token_count >= 1000
                chunked_takeaway_lists.append([{"message": takeaway.title}])
                token_count = 0

        # Call OpenAI
        try:
            with get_openai_callback() as callback:
                results = []
                for takeaway_list in chunked_takeaway_lists:
                    data = {"takeaways": takeaway_list}
                    takeaways = json.dumps(data)
                    result = chain.invoke({"takeaways": takeaways})
                    pprint(result["function"])
                    results.extend(result["function"]["takeaways"])
                note.analyzing_tokens += callback.total_tokens
                note.analyzing_cost += Decimal(callback.total_cost)
            note.save()
        except:
            import traceback

            traceback.print_exc()
            return Response(
                {"details": "Failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Save tags
        tags_to_add = [
            Tag(name=tag_name, project=note.project)
            for takeaway in results
            for tag_name in takeaway["tags"]
        ]
        Tag.objects.bulk_create(tags_to_add, ignore_conflicts=True)
        tag_names = [tag.name for tag in tags_to_add]
        tags = Tag.objects.filter(name__in=tag_names, project=note.project)

        # Save takeaway tags
        get_tag = {tag.name.lower(): tag for tag in tags}
        get_takeaway = {
            unidecode(takeaway.title): takeaway for takeaway in note.takeaways.all()
        }
        TakeawayTag = Takeaway.tags.through
        takeaway_tags = []
        for takeaway_data in results:
            takeaway: Takeaway = get_takeaway[unidecode(takeaway_data["message"])]
            for tag_name in takeaway_data["tags"]:
                tag = get_tag[tag_name.lower()]
                takeaway_tags.append(TakeawayTag(takeaway=takeaway, tag=tag))
        TakeawayTag.objects.bulk_create(takeaway_tags, ignore_conflicts=True)

        # Update takeaway_count
        tags = Tag.objects.filter(name__in=tag_names, project=note.project).annotate(
            new_takeaway_count=Count("takeaways")
        )
        for tag in tags:
            tag.takeaway_count = tag.new_takeaway_count
        Tag.objects.bulk_update(tags, ["takeaway_count"])

        return Response({"details": "Successful"})
