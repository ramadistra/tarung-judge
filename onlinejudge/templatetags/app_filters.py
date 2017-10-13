from django import template


register = template.Library()


@register.filter(name='is_solved')
def is_solved(question, user):
    return question.is_solved_by(user) 
