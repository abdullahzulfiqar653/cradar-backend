from django.conf import settings
from django.http import HttpResponseRedirect
from rest_framework import generics
from rest_framework.permissions import AllowAny


class SlackToFrontendRedirectView(generics.GenericAPIView):
    # This view is only for local testing, not used in production
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        return HttpResponseRedirect(
            f"{settings.FRONTEND_URL}/slack/redirect?code={code}&state={state}"
        )
