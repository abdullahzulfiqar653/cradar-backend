from contextlib import contextmanager
from decimal import Decimal

from langchain.callbacks import get_openai_callback
from langchain.callbacks.base import BaseCallbackHandler

from api.models.usage.token import TokenUsage


@contextmanager
def token_tracker(project, content_object, action, created_by):
    with get_openai_callback() as callback:
        try:
            yield callback
        finally:
            TokenUsage.objects.create(
                workspace=project.workspace,
                project=project,
                content_object=content_object,
                action=action,
                created_by=created_by,
                value=callback.total_tokens,
                cost=Decimal(callback.total_cost),
            )


class ParserErrorCallbackHandler(BaseCallbackHandler):
    def on_chain_start(self, *args, **kwargs):
        if kwargs.get("run_type") == "parser":
            self.ai_message = args[1]

    def on_chain_error(self, *args, **kwargs):
        if hasattr(self, "ai_message"):
            print(self.ai_message)
