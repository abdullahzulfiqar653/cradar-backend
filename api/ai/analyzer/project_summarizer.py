from api.ai.generators.project_clusterer import cluster_project
from api.ai.generators.project_summarizer import summarize_project
from api.models.project import Project


class ProjectSummarizer:
    def summarize_all_projects(self, created_by):
        for project in Project.objects.all():
            print(f"Summarizing project <{project.id}: {project.name}>")
            summarize_project(project, created_by)
            cluster_project(project, created_by)
