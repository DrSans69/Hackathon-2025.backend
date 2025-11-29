from rest_framework.decorators import api_view
from rest_framework.response import Response

from shared.utils import handle_error

from .ai import do


@api_view(["GET"])
def hello(request):
    try:

        return Response({"message": do()})

    except Exception as e:
        return handle_error()
