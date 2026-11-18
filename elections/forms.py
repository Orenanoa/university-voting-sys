from django import forms

from .models import Ballot, Candidate, Election, Position, Student, Voter


class BaseForm(forms.ModelForm):
    """Shared setup: '-- Select --' in dropdowns, and show the id of the record being edited."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field, forms.ModelChoiceField):
                field.empty_label = '-- Select --'
            elif isinstance(field, forms.ChoiceField):
                field.choices = [('', '-- Select --')] + [c for c in field.choices if c[0] != '']
        if self.instance.pk:
            for name in ('election_id', 'position_id', 'candidate_id', 'voter_id', 'voters'):
                if name in self.fields:
                    self.fields[name].initial = getattr(self.instance, name)


class StudentForm(BaseForm):
    class Meta:
        model = Student
        fields = ['student_id', 'first_name', 'last_name', 'student_gender',
                  'course', 'year_of_study', 'session']
        labels = {'student_id': 'Student ID', 'first_name': 'First Name', 'last_name': 'Last Name',
                  'student_gender': 'Gender', 'year_of_study': 'Year of Study'}


class ElectionForm(BaseForm):
    election_id = forms.CharField(label='Election ID', required=False, disabled=True, initial='Auto-generated')
    voters = forms.IntegerField(label='Voters (registered)', required=False, disabled=True, initial=0)

    class Meta:
        model = Election
        fields = ['title', 'status']

    field_order = ['election_id', 'title', 'voters', 'status']


class PositionForm(BaseForm):
    position_id = forms.CharField(label='Position ID', required=False, disabled=True, initial='Auto-generated')

    class Meta:
        model = Position
        fields = ['election', 'title', 'description']
        widgets = {'description': forms.Textarea(attrs={'placeholder': 'What does this position do?'})}

    field_order = ['position_id', 'election', 'title', 'description']


class CandidateForm(BaseForm):
    candidate_id = forms.CharField(label='Candidate ID', required=False, disabled=True, initial='Auto-generated')

    class Meta:
        model = Candidate
        fields = ['student', 'candidate_position', 'candidate_voter', 'status']
        labels = {'candidate_position': 'Candidate Position',
                  'candidate_voter': 'Candidate Voter (voter ID)'}

    field_order = ['candidate_id', 'student', 'candidate_position', 'candidate_voter', 'status']


class VoterForm(BaseForm):
    voter_id = forms.CharField(label='Voter ID', required=False, disabled=True, initial='Auto-generated')

    class Meta:
        model = Voter
        fields = ['election', 'student', 'voter_age', 'position']
        labels = {'voter_age': 'Voter Age'}

    field_order = ['voter_id', 'election', 'student', 'voter_age', 'position']


class BallotForm(BaseForm):
    class Meta:
        model = Ballot
        fields = ['voter', 'election', 'position', 'candidate']
        labels = {'voter': 'Voter ID', 'candidate': 'Candidate Name'}
