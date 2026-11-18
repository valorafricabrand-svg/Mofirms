from django.db import migrations


AUTHOR_NAME = "Vofa"
ROLE = "Mushroom farmer, Valor Africa Limited"
QUOTE = (
    "MoFirms helped us put real numbers behind our mushroom farming "
    "venture before we committed any capital. Their financial "
    "analysis gave Valor Africa Limited the confidence to grow from "
    "a small trial into a proper production line."
)


def remove_testimonial(apps, schema_editor):
    Testimonial = apps.get_model("farmers", "Testimonial")
    Testimonial.objects.filter(author_name=AUTHOR_NAME, role=ROLE).delete()


def restore_testimonial(apps, schema_editor):
    Testimonial = apps.get_model("farmers", "Testimonial")
    Testimonial.objects.get_or_create(
        author_name=AUTHOR_NAME,
        role=ROLE,
        defaults={"quote": QUOTE, "display_order": 0},
    )


class Migration(migrations.Migration):

    dependencies = [
        ("farmers", "0018_seed_testimonials"),
    ]

    operations = [
        migrations.RunPython(remove_testimonial, restore_testimonial),
    ]
