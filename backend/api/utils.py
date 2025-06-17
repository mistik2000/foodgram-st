from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return response

    if response.status_code == status.HTTP_400_BAD_REQUEST:
        if isinstance(response.data, dict):
            errors = []
            for field, error_list in response.data.items():
                if isinstance(error_list, list):
                    for error in error_list:
                        errors.append(f'{field}: {error}')
                else:
                    errors.append(f'{field}: {error_list}')
            response.data = {'errors': errors}
        elif isinstance(response.data, list):
            response.data = {'errors': response.data}

    return response 