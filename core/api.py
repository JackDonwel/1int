from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404
from core.models import StampApplication  # Adjust the import path based on your project structure
import hashlib

@api_view(['GET'])
def qr_metadata(request, application_id):
    application = get_object_or_404(StampApplication, id=application_id)
    return Response({
        "advocate_id": application.user.tls_id,
        "stamp_type": application.stamp_type,
        "issue_date": application.approved_date.isoformat(),
        "security_hash": hashlib.sha256(
            f"{application.id}{application.user.id}".encode()
        ).hexdigest()
    })