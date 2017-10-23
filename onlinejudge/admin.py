from django.contrib import admin

from .models import Question, Case, Attempt, Category, Contest, User

class ChoiceInline(admin.StackedInline):
    model = Case
    extra = 3


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['title', 'contest', 'category', 'difficulty', 'description', 'template', ]}),
        ('Details',          {'fields': ['author', 'slug', 'published_date']}),
    ]
    inlines = [ChoiceInline]

    def save_model(self, request, obj, form, change):
        if obj.author is None:
            obj.author = request.user
        super(QuestionAdmin, self).save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        '''
        Override to make certain fields readonly if this is a change request
        '''
        if request.user.is_superuser:
            return self.readonly_fields
        return self.readonly_fields  + ('author',)

admin.site.register(Question, QuestionAdmin)
admin.site.register(Attempt)
admin.site.register(Category)
admin.site.register(Contest)
