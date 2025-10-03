from typing import List, Type, Union

from django.utils.decorators import method_decorator

from rest_framework.serializers import Serializer
from rest_framework.views import APIView

from drf_yasg.inspectors import FieldInspector, SwaggerAutoSchema
from drf_yasg.openapi import Parameter, Schema, SchemaRef
from drf_yasg.utils import swagger_auto_schema, unset

CALLBACKS_TAG = 'callbacks'


def define_swagger_auto_schema(
    api_view: Type[APIView],
    method_name: str,
    tags: List[str] = None,
    operation_id: str = None,
    operation_description: str = None,
    operation_summary: str = None,
    auto_schema: SwaggerAutoSchema = unset,
    request_body: Union[Schema, SchemaRef, Serializer, type] = None,
    query_serializer: Union[Type[Serializer], Serializer] = None,
    manual_parameters: List[Parameter] = None,
    responses: dict = None,
    field_inspectors: List[Type[FieldInspector]] = None,
    **extra_overrides
):
    """Function to define hooks for swagger autoschema.

    This is simple shortcut wrapper on `swagger_auto_schema`, which passed
    most params to it.

    It needed to have single place for schema defining.

    Use it in `scheme.py` file of `api` folder of app you working on.
    If you working on `new` app, then don't forget to add import of `scheme.py`
    file to  the `app config`

    Arguments:
        api_view (Type[APIView]): APIView that needs swagger spec customization
        method_name (str): Name of action or method that needs swagger spec to
        be overridden.
        tags (List[str]): List of tags for api method
        operation_id (str): Id of api method in swagger spec
        operation_description (str): Description of api method
        operation_summary (str): Summary of api method
        auto_schema (SwaggerAutoSchema):
            Custom class what will be used for generating the Operation object
        request_body (Schema, SchemaRef, Serializer, type): Custom request body
        query_serializer (Type[Serializer], Serializer):
            To add custom query params to swagger spec
        manual_parameters (List[Parameter]):
            A list of manual parameters to override the automatically generated
            ones
        responses (dict):
            Dictionary for custom responses where key is status code and
            value is  SchemaRef, Serializer, string or None.
        field_inspectors (List[Type[FieldInspector]]):
            Extra serializer and field inspectors

    Examples of usages:
        Simple example:
            define_swagger_auto_schema(
                api_view=APIView,
                method_name='update',
                # Add your params
            )
        Customization of responses:
            define_swagger_auto_schema(
                api_view=views.ESignCallbacksView,
                method_name='save_consent',
                responses={
                    '302': None,
                    '400': 'Invalid data',
                    '200': serializers.ESignProfileSerializer
                }
            )
        Custom query params:
            define_swagger_auto_schema(
                api_view=views.MediatorViewSet,
                method_name='validate_registration',
                query_serializer=serializers.MediatorRegisterValidateSerializer
            )
        Make method do not require any data:
            define_swagger_auto_schema(
                api_view=views.MatterViewSet,
                method_name='revoke',
                request_body=no_body,
            )
    """
    method_decorator(
        name=method_name,
        decorator=swagger_auto_schema(
            tags=tags,
            operation_id=operation_id,
            operation_description=operation_description,
            operation_summary=operation_summary,
            auto_schema=auto_schema,
            request_body=request_body,
            query_serializer=query_serializer,
            manual_parameters=manual_parameters,
            responses=responses,
            field_inspectors=field_inspectors,
            **extra_overrides
        ),
    )(api_view)
