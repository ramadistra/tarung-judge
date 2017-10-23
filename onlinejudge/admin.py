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


class AttemptAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        # Make all fields read-only.
        return self.readonly_fields + tuple(f.name for f in obj._meta.get_fields())


admin.site.register(Question, QuestionAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Category)
admin.site.register(Contest)
