from rest_framework import renderers
import json

class UserRenderers(renderers.JSONRenderer):
    """
    Custom JSON renderer for user-related responses.

    This renderer handles JSON serialization for responses related to user operations,
    ensuring consistent formatting and handling of error messages.

    Attributes:
        charset (str): Character encoding for the rendered content ('utf-8' by default).
    """

    charset = 'utf-8'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        """
        Render the given data into JSON format.

        Args:
            data (dict or list): Data to be serialized into JSON.
            accepted_media_type (str): Accepted media type (unused in this implementation).
            renderer_context (dict): Contextual information for rendering (unused in this implementation).

        Returns:
            str: JSON-encoded string representing the serialized data.
        """
        response = ''
        if "ErrorDetail" in str(data):
            # If the response contains error details, wrap them in an 'errors' key.
            response = json.dumps({'errors': data})
        else:
            # Otherwise, serialize the data normally.
            response = json.dumps(data)
        return response