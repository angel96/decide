from django.contrib import admin
from django.utils import timezone

from .models import Voting
from .models import Candidate
from .models import CandidatesGroup
from .filters import StartedFilter


def start(modeladmin, request, queryset):
    for v in queryset.all():
        v.create_pubkey()
        v.start_date = timezone.now()
        v.save()


def stop(ModelAdmin, request, queryset):
    for v in queryset.all():
        v.end_date = timezone.now()
        v.save()


def tally(ModelAdmin, request, queryset):
    for v in queryset.filter(end_date__lt=timezone.now()):
        token = request.session.get('auth-token', '')
        v.tally_votes(token)


#class QuestionOptionInline(admin.TabularInline):
#    model = QuestionOption


#class QuestionAdmin(admin.ModelAdmin):
#    inlines = [QuestionOptionInline]


class VotingAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'start_date_selected', 'end_date_selected')
    readonly_fields = ('start_date', 'end_date', 'pub_key',
                       'tally', 'postproc')
    date_hierarchy = 'start_date'
    list_filter = (StartedFilter,)
    search_fields = ('name', )

    actions = [ start, stop, tally ]

class CandidateAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'born_area', 'current_area', 'primaries', 'sex', 'candidatesGroup',)

class CandidateGroupAdmin(admin.ModelAdmin):
    list_display = ('name',)

admin.site.register(Candidate, CandidateAdmin)
admin.site.register(CandidatesGroup, CandidateGroupAdmin)
admin.site.register(Voting, VotingAdmin)
#admin.site.register(Question, QuestionAdmin)
