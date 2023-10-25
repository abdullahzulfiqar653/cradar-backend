import json
from threading import Thread
from time import time

from django.core.files.uploadedfile import UploadedFile
from django.db.models import Count, F
from django.http.request import QueryDict
from django.shortcuts import get_object_or_404
from rest_framework import exceptions, generics, serializers, status
from rest_framework.response import Response

from note.filters import NoteFilter
from note.models import Note
from note.serializers import ProjectNoteSerializer, NoteCompanySerializer
from project.models import Project
from project.serializers import ProjectSerializer
from tag.models import Tag
from tag.serializers import TagSerializer
from takeaway.filters import TakeawayFilter
from takeaway.models import Takeaway
from takeaway.serializers import TakeawaySerializer
from transcriber.transcribers import omni_transcriber
from user.serializers import AuthUserSerializer

from .models import Project
from .summarizers import RefineSummarizer

transcriber = omni_transcriber
summarizer = RefineSummarizer()


class ProjectListCreateView(generics.ListCreateAPIView):
    # TODO: To be deprecated and replaced WorkspaceProjectListCreateView
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    ordering = ['-created_at']

    def get_queryset(self):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        return Project.objects.filter(workspace=workspace, users=auth_user)
    
    def create(self, request, *args, **kwargs):
        auth_user = self.request.user
        workspace = auth_user.workspaces.first()
        if workspace.projects.count() > 1:
            # We restrict user from creating more than 2 projects per workspace
            raise exceptions.PermissionDenied('Cannot create more than 2 projects in one workspace.')
        return super().create(request, *args, **kwargs)

class ProjectRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

class ProjectAuthUserListView(generics.ListAPIView):
    serializer_class = AuthUserSerializer
    ordering = ['last_name']
    search_fields = [
        'username',
        'first_name',
        'last_name',
    ]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return project.users.all()

    
class ProjectNoteListCreateView(generics.ListCreateAPIView):
    queryset = Note.objects.all()
    serializer_class = ProjectNoteSerializer
    filterset_class = NoteFilter
    ordering_fields = [
        'created_at', 
        'takeaway_count', 
        'author__first_name', 
        'author__last_name', 
        'company_name',
        'title',
    ]
    search_fields = [
        'title',
        'author__username',
        'author__first_name',
        'author__last_name',
        'company_name',
    ]
    ordering = ['-created_at']

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        return (
            project.notes
            .annotate(takeaway_count=Count('takeaways'))
            .annotate(participant_count=Count('user_participants'))
        )
    
    def get_project(self):
        project_id = self.kwargs.get('project_id')
        project = get_object_or_404(Project, id=project_id)
        if not project.users.contains(self.request.user):
            raise exceptions.PermissionDenied
        return project
    
    def to_dict(self, form_data):
        data_file = form_data.get('data')
        if not isinstance(data_file, UploadedFile):
            raise serializers.ValidationError('`data` field must be a blob.')
        data = json.load(data_file)
        data['file'] = form_data.get('file')
        return data

    
    def get_serializer(self, *args, **kwargs):
        # Convert data to json if the request is multipart form
        data = kwargs.get('data')
        
        if data is None:
            # If it is not POST request, data is None
            return super().get_serializer(*args, **kwargs)

        if isinstance(data, QueryDict):
            kwargs['data'] = self.to_dict(data)
            data = kwargs['data']

        # In multipart form, null will be treated as string instead of converting to None
        # We need to manually handle the null
        if 'revenue' not in data or data['revenue'] == 'null':
            data['revenue'] = None

        if 'file' not in data or data['file'] == 'null':
            data['file'] = None

        return super().get_serializer(*args, **kwargs)
    
    def perform_create(self, serializer):
        project = self.get_project()
        note = serializer.save(author=self.request.user, project=project)
        if note.file:
            thread = Thread(
                target=self.analyze,
                kwargs={'note': note},
            )
            thread.start()

    def transcribe(self, note):
        filepath = note.file.path
        filetype = note.file_type
        transcript = transcriber.transcribe(filepath, filetype)
        if transcript is not None:
            note.content = transcript
            note.save()

    def summarize(self, note):
        text = f'{note.title}\n{note.content}'
        insight = summarizer.summarize(text)
        note.summary = insight['summary']
        note.sentiment = insight['sentiment']
        note.save()
        for keyword in insight['keywords']:
            tag, is_created = Tag.objects.get_or_create(name=keyword)
            note.tags.add(tag)
        for takeaway_title in insight['takeaways']:
            takeaway = Takeaway(title=takeaway_title, note=note)
            takeaway.save()


    def analyze(self, note):
        note.is_analyzing = True
        note.save()
        try:
            print('========> Start transcribing')
            start = time()
            self.transcribe(note)
            end = time()
            print(f'Elapsed time: {end - start} seconds')
            print('========> Start summarizing')
            self.summarize(note)
            print('========> End analyzing')
        except Exception as e:
            import traceback
            traceback.print_exc()
        note.is_analyzing = False
        note.save()
    
class ProjectTakeawayListView(generics.ListAPIView):
    serializer_class = TakeawaySerializer
    filterset_class = TakeawayFilter
    ordering_fields = [
        'created_at', 
        'created_by__first_name', 
        'created_by__last_name', 
        'title',
    ]
    ordering = ['created_at']
    search_fields = [
        'title',
        'created_by__username',
        'created_by__first_name',
        'created_by__last_name',
    ]

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return Takeaway.objects.filter(note__project=project)
    

class ProjectTakeawayTagListView(generics.ListAPIView):
    serializer_class = TagSerializer
    ordering = ['name']

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound

        return Tag.objects.filter(takeaway__note__project=project)


class ProjectCompanyListView(generics.ListAPIView):
    serializer_class = NoteCompanySerializer
    ordering = ['name']

    def get_queryset(self):
        project_id = self.kwargs['project_id']
        project = self.request.user.projects.filter(id=project_id).first()
        if project is None:
            raise exceptions.NotFound
        
        return (
            Note.objects
            .filter(project=project)
            .annotate(name=F('company_name'))
            .values('name')
            .distinct()
        )
    