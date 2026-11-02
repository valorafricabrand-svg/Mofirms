from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import (
    FarmerDocument,
    FinancialAnalysisDocument,
    PartnerDocument,
    RiskAssessmentDocument,
)


@receiver(post_delete, sender=FarmerDocument)
@receiver(post_delete, sender=PartnerDocument)
@receiver(post_delete, sender=FinancialAnalysisDocument)
@receiver(post_delete, sender=RiskAssessmentDocument)
def remove_private_document_file(sender, instance, **kwargs):
    if instance.file:
        storage = instance.file.storage
        name = instance.file.name
        transaction.on_commit(lambda: storage.delete(name))
