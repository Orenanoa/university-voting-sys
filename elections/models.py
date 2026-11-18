from django.core.exceptions import ValidationError
from django.db import models


class Student(models.Model):
    GENDER_CHOICES = [('Male', 'Male'), ('Female', 'Female')]
    YEAR_CHOICES = [(1, 'Year 1'), (2, 'Year 2'), (3, 'Year 3'), (4, 'Year 4')]
    SESSION_CHOICES = [('Day', 'Day'), ('Evening', 'Evening'), ('Weekend', 'Weekend')]

    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    student_gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    course = models.CharField(max_length=100)
    year_of_study = models.PositiveSmallIntegerField(choices=YEAR_CHOICES)
    session = models.CharField(max_length=10, choices=SESSION_CHOICES)

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f'{self.student_id} - {self.full_name()}'

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def register(self):
        """Register() - save the student in the register."""
        self.save()
        return self


class Election(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Ongoing', 'Ongoing'), ('Ended', 'Ended')]

    title = models.CharField(max_length=150)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.title

    @property
    def election_id(self):
        return self.pk

    @property
    def voters(self):
        """Number of voters registered for this election."""
        return self.registered_voters.count()

    def start_election(self):
        self.status = 'Ongoing'
        self.save()

    def end_election(self):
        self.status = 'Ended'
        self.save()

    def display_candidates(self):
        return Candidate.objects.filter(candidate_position__election=self)


class Position(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='positions')
    title = models.CharField(max_length=100)
    description = models.TextField()

    class Meta:
        ordering = ['election', 'id']

    def __str__(self):
        return self.title

    @property
    def position_id(self):
        return self.pk

    def add_candidate(self, student, voter, status='Pending'):
        candidate, created = Candidate.objects.get_or_create(
            student=student, candidate_position=self,
            defaults={'candidate_voter': voter, 'status': status})
        return candidate

    def display_candidates(self):
        return self.candidates.all()


class Voter(models.Model):
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='registered_voters')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='voter_records')
    voter_age = models.PositiveSmallIntegerField()
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='position_voters')

    class Meta:
        ordering = ['id']
        unique_together = ['election', 'student']

    def __str__(self):
        return f'{self.pk} - {self.student.full_name()}'

    @property
    def voter_id(self):
        return self.pk

    def clean(self):
        if self.voter_age is not None and self.voter_age < 18:
            raise ValidationError({'voter_age': 'A voter must be 18 or older.'})
        if self.election_id and self.position_id and self.position.election_id != self.election_id:
            raise ValidationError('That position does not belong to the selected election.')

    def register(self):
        self.save()
        return self

    def vote(self, candidate):
        """Vote() - cast a ballot for a candidate. Returns (ok, message)."""
        ballot = Ballot(voter=self, election=self.election,
                        position=candidate.candidate_position, candidate=candidate)
        return ballot.submit_ballot()


class Candidate(models.Model):
    STATUS_CHOICES = [('Pending', 'Pending'), ('Approved', 'Approved'), ('Disqualified', 'Disqualified')]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='candidacies')
    candidate_position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='candidates')
    candidate_voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='candidacies')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='Pending')

    class Meta:
        ordering = ['id']
        unique_together = ['student', 'candidate_position']

    def __str__(self):
        return f'{self.student.full_name()} ({self.candidate_position})'

    @property
    def candidate_id(self):
        return self.pk

    def votes(self):
        return self.ballots.count()

    def display_information(self):
        return (f'{self.student.full_name()} is standing for {self.candidate_position} '
                f'in {self.candidate_position.election}. Status: {self.status}.')

    def receive_vote(self, voter):
        """Receive_vote() - record a vote from a voter. Returns (ok, message)."""
        ballot = Ballot(voter=voter, election=voter.election,
                        position=self.candidate_position, candidate=self)
        return ballot.submit_ballot()


class Ballot(models.Model):
    voter = models.ForeignKey(Voter, on_delete=models.CASCADE, related_name='ballots')
    election = models.ForeignKey(Election, on_delete=models.CASCADE, related_name='ballots')
    position = models.ForeignKey(Position, on_delete=models.CASCADE, related_name='ballots')
    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='ballots')

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f'Ballot {self.pk}: voter {self.voter_id} -> {self.candidate_name}'

    @property
    def candidate_name(self):
        return self.candidate.student.full_name()

    def validate_ballot(self):
        """Validate_ballot() - returns (True/False, message)."""
        if None in (self.voter_id, self.election_id, self.position_id, self.candidate_id):
            return False, 'Fill in every field.'
        if self.election.status != 'Ongoing':
            return False, 'This election is not ongoing, so voting is closed.'
        if self.voter.election_id != self.election_id:
            return False, 'This voter is not registered for the selected election.'
        if self.position.election_id != self.election_id:
            return False, 'That position does not belong to the selected election.'
        if self.candidate.candidate_position_id != self.position_id:
            return False, 'That candidate is not standing for the selected position.'
        if self.candidate.status != 'Approved':
            return False, 'That candidate has not been approved.'
        already = Ballot.objects.filter(voter=self.voter, position=self.position).exclude(pk=self.pk)
        if already.exists():
            return False, 'This voter has already voted for this position.'
        return True, 'Ballot is valid and ready to submit.'

    def clean(self):
        if None in (self.voter_id, self.election_id, self.position_id, self.candidate_id):
            return
        ok, message = self.validate_ballot()
        if not ok:
            raise ValidationError(message)

    def submit_ballot(self):
        """Submit_ballot() - save the ballot if it is valid."""
        ok, message = self.validate_ballot()
        if ok:
            self.save()
        return ok, message
