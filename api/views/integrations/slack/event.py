from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers.integrations.slack.event import SlackEventSerializer


class SlackEventsCreateView(APIView):
    serializer_class = SlackEventSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        raw_body = request.body.decode("utf-8")
        serializer = SlackEventSerializer(
            data=request.data, context={"request": request, "raw_body": raw_body}
        )
        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        if serializer.validated_data.get("type") == "url_verification":
            return Response({"challenge": serializer.validated_data["challenge"]})

        return Response({"status": "OK"})
