from django.db import migrations


TESTIMONIALS = [
    {
        "author_name": "Mushroom farming client",
        "role": "Mushroom farmer, Valor Africa Limited",
        "quote": (
            "MoFirms helped us put real numbers behind our mushroom farming "
            "venture before we committed any capital. Their financial "
            "analysis gave Valor Africa Limited the confidence to grow from "
            "a small trial into a proper production line."
        ),
        "display_order": 0,
    },
    {
        "author_name": "Vihiga Organic Farmers Association (VOFA)",
        "role": "Organic farmers' cooperative, Vihiga County",
        "quote": (
            "As an organic farmers' association in Vihiga, we needed a "
            "clear way to see which crops were actually paying off for our "
            "members. MoFirms' business readiness check helped us organise "
            "our records and plan our season with real numbers instead of "
            "guesswork."
        ),
        "display_order": 3,
    },
]


def add_testimonials(apps, schema_editor):
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
        ("farmers", "0019_remove_vofa_testimonial"),
    ]

    operations = [
        migrations.RunPython(add_testimonials, remove_testimonials),
    ]
