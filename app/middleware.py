import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('app.request')

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        user = request.user if hasattr(request, 'user') and request.user.is_authenticated else 'Anonymous'
        logger.info(
            '%s %s %s %s',
            request.method,
            request.get_full_path(),
            user,
            response.status_code,
        )
        return response
