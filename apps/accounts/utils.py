from rest_framework_simplejwt.tokens import RefreshToken


def get_token_for_user(user):
    """
    Generate JWT tokens for the given user.

    This function generates both refresh and access tokens for the provided user
    using the Simple JWT library.

    Args:
        user (CustomUser): The user object for whom tokens are generated.

    Returns:
        dict: A dictionary containing the refresh and access tokens as strings.

    Example return:
        {
            'refresh': '<refresh_token_string>',
            'access': '<access_token_string>'
        }
    """
    # Generate a refresh token for the user
    refresh = RefreshToken.for_user(user)

    # Return a dictionary with the refresh and access tokens as strings
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token)
    }
