from django import template


register = template.Library()


@register.filter
def research_question_field(form, question_id):
    return form[f"question_{question_id}"]
