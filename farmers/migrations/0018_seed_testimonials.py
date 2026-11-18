from django.db import migrations


TESTIMONIALS = [
    {
        "author_name": "Beekeeping client",
        "role": "Beekeeper, Narok",
        "quote": (
            "I used to manage my hives on guesswork. With MoFirms' business "
            "readiness check, I finally understood my real costs and where "
            "the honey business was losing money, and where it could grow."
        ),
        "display_order": 1,
    },
    {
        "author_name": "Fish farming client",
        "role": "Fish grower, Kisumu",
        "quote": (
            "Our fish ponds in Kisumu were productive, but we had no clear "
            "records. MoFirms walked us through proper record keeping and "
            "risk assessment, so we now plan feeding and sales with "
            "confidence instead of guessing."
        ),
        "display_order": 2,
    },
]


def seed_testimonials(apps, schema_editor):
    Testimonial = apps.get_model("farmers", "Testimonial")
    for entry in TESTIMONIALS:
        Testimonial.objects.get_or_create(
            author_name=entry["author_name"],
            role=entry["role"],
            defaults={"quote": entry["quote"], "display_order": entry["display_order"]},
        )


def remove_testimonials(apps, schema_editor):
    Testimonial = apps.get_model("farmers", "Testimonial")
    for entry in TESTIMONIALS:
        Testimonial.objects.filter(
            author_name=entry["author_name"], role=entry["role"]
        ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("farmers", "0017_testimonial"),
    ]

    operations = [
        migrations.RunPython(seed_testimonials, remove_testimonials),
    ]
