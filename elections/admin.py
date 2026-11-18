from django.contrib import admin

from .models import Ballot, Candidate, Election, Position, Student, Voter

admin.site.site_header = 'IUIU Voting System Admin'
admin.site.site_title = 'IUIU Voting System'
admin.site.index_title = 'Manage the election data'


class PositionInline(admin.TabularInline):
    model = Position
    extra = 1


class CandidateInline(admin.TabularInline):
    model = Candidate
    extra = 1


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'first_name', 'last_name', 'student_gender', 'course', 'year_of_study', 'session')
    list_filter = ('student_gender', 'year_of_study', 'session')
    search_fields = ('student_id', 'first_name', 'last_name', 'course')


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'voters')
    list_filter = ('status',)
    search_fields = ('title',)
    inlines = [PositionInline]
    actions = ['start_elections', 'end_elections']

    @admin.action(description='Start selected elections')
    def start_elections(self, request, queryset):
        for election in queryset:
            election.start_election()
        self.message_user(request, f'{queryset.count()} election(s) started.')

    @admin.action(description='End selected elections')
    def end_elections(self, request, queryset):
        for election in queryset:
            election.end_election()
        self.message_user(request, f'{queryset.count()} election(s) ended.')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('title', 'election', 'description')
    list_filter = ('election',)
    search_fields = ('title',)
    inlines = [CandidateInline]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('student', 'candidate_position', 'candidate_voter', 'status')
    list_filter = ('status', 'candidate_position')
    search_fields = ('student__first_name', 'student__last_name')


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'election', 'voter_age', 'position')
    list_filter = ('election',)
    search_fields = ('student__first_name', 'student__last_name')


@admin.register(Ballot)
class BallotAdmin(admin.ModelAdmin):
    list_display = ('id', 'voter', 'election', 'position', 'candidate')
    list_filter = ('election', 'position')
