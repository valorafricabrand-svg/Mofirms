from django.db import migrations


def rename_accelerator_plan(apps, schema_editor):
    ServicePlan = apps.get_model("farmers", "ServicePlan")
    ServicePlan.objects.filter(slug="verified-accelerator").update(
        slug="enterprise-accelerator",
        name="Enterprise Accelerator",
    )


class Migration(migrations.Migration):
    dependencies = [
        ("farmers", "0010_alter_betaenrollment_invite_and_more"),
    ]

    operations = [
        migrations.RunPython(rename_accelerator_plan, migrations.RunPython.noop),
    ]
