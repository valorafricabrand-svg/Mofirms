from django.db import transaction
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver

from .models import (
    BetaEnrollment,
    FarmerDocument,
    FinancialAnalysisDocument,
    MpesaPayment,
    PartnerDocument,
    RiskAssessmentDocument,
)
from .mpesa import mask_phone_number


@receiver(post_delete, sender=FarmerDocument)
@receiver(post_delete, sender=PartnerDocument)
@receiver(post_delete, sender=FinancialAnalysisDocument)
@receiver(post_delete, sender=RiskAssessmentDocument)
def remove_private_document_file(sender, instance, **kwargs):
    if instance.file:
        storage = instance.file.storage
        name = instance.file.name
        transaction.on_commit(lambda: storage.delete(name))


@receiver(pre_delete, sender=BetaEnrollment)
def anonymize_beta_payments_before_profile_retention(sender, instance, **kwargs):
    for payment in instance.payments.all():
        payment.phone_number = mask_phone_number(payment.phone_number)
        if payment.status in {MpesaPayment.Status.INITIATING, MpesaPayment.Status.PENDING}:
            payment.status = MpesaPayment.Status.FAILED
            payment.result_description = (
                "Beta access closed before payment confirmation."
            )
        payment.save(
            update_fields=[
                "phone_number",
                "status",
                "result_description",
                "updated_at",
            ]
        )
