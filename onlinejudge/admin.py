from django.contrib import admin

from .models import Question, Case, Attempt, Category, Contest

class ChoiceInline(admin.StackedInline):
    model = Case
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'contest', 'category', 'difficulty', 'description', 'template']}),
        ('Details',          {'fields': ['slug', 'published_date']}),
    ]
    inlines = [ChoiceInline]

admin.site.register(Question, QuestionAdmin)
admin.site.register(Attempt)
admin.site.register(Category)
admin.site.register(Contest)
