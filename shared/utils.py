import sys

from rest_framework.response import Response

from logging import getLogger


def handle_error(
    context: str | None = None,
    response: str | None = None,
    status: int = 400,
) -> Response:
    DEFAULT_MSG = "Unexpected error"
    exc_type, exc_value, exc_traceback = sys.exc_info()

    base_msg = response or context or DEFAULT_MSG

    if exc_value:
        error_msg = f"{base_msg}: {exc_value}"
        # logger.exception(context or DEFAULT_MSG)
    else:
        error_msg = base_msg
        # logger.error(context or DEFAULT_MSG)

    print(error_msg)
    return Response({"error": error_msg}, status=status)


def handle_success(response: str) -> Response:
    # logger.info(response)
    print(response)
    return Response({"message": response})
