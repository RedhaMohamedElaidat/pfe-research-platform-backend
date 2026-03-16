from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .ai_engine import process_question


class ChatbotView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        question = request.data.get("message")

        answer = process_question(question)

        return Response({
            "question": question,
            "answer": answer
        })