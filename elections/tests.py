from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import Ballot, Candidate, Election, Student, Voter


class VotingSystemTests(TestCase):
    def setUp(self):
        call_command('load_dummy_data', verbosity=0)
        User.objects.create_user('staff1', password='pass12345', is_staff=True)
        User.objects.create_user('user1', password='pass12345')
        self.election = Election.objects.get(title='Guild Elections 2026')
        self.aisha = Candidate.objects.get(student__first_name='Aisha')
        self.ibrahim_voter = Voter.objects.get(student__first_name='Ibrahim')

    def login(self, name):
        self.client.login(username=name, password='pass12345')

    def vote_data(self, voter, candidate, action='save'):
        return {'voter': voter.pk, 'election': self.election.pk,
                'position': candidate.candidate_position_id, 'candidate': candidate.pk, 'action': action}

    def test_login_is_required(self):
        self.assertEqual(self.client.get(reverse('students')).status_code, 302)

    def test_every_page_opens_for_staff(self):
        self.login('staff1')
        for name in ['home', 'students', 'election', 'position', 'candidate', 'voter', 'ballot', 'results']:
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)

    def test_dummy_data_has_five_rows_each(self):
        for model in (Student, Election, Voter, Candidate, Ballot):
            self.assertEqual(model.objects.count(), 5)

    def test_staff_can_create_edit_delete_student(self):
        self.login('staff1')
        data = {'student_id': 'S010', 'first_name': 'Test', 'last_name': 'Student', 'student_gender': 'Male',
                'course': 'Law', 'year_of_study': 2, 'session': 'Day'}
        self.client.post(reverse('students'), data)
        student = Student.objects.get(student_id='S010')
        data['first_name'] = 'Changed'
        self.client.post(reverse('students_edit', args=[student.pk]), data)
        student.refresh_from_db()
        self.assertEqual(student.first_name, 'Changed')
        self.client.post(reverse('students_delete', args=[student.pk]))
        self.assertFalse(Student.objects.filter(student_id='S010').exists())

    def test_normal_user_cannot_add_student(self):
        self.login('user1')
        self.client.post(reverse('students'), {'student_id': 'S011', 'first_name': 'No', 'last_name': 'Way',
                                               'student_gender': 'Male', 'course': 'Law',
                                               'year_of_study': 1, 'session': 'Day'})
        self.assertFalse(Student.objects.filter(student_id='S011').exists())

    def test_voter_must_be_18(self):
        self.login('staff1')
        student = Student.objects.get(first_name='Aisha')
        position = self.aisha.candidate_position
        count = Voter.objects.count()
        self.client.post(reverse('voter'), {'election': self.election.pk, 'student': student.pk,
                                            'voter_age': 15, 'position': position.pk})
        self.assertEqual(Voter.objects.count(), count)

    def test_ballot_rules(self):
        self.login('user1')   # normal users may vote
        # valid ballot is saved
        self.client.post(reverse('ballot'), self.vote_data(self.ibrahim_voter, self.aisha))
        self.assertEqual(Ballot.objects.count(), 6)
        # voting twice for the same position is refused
        self.client.post(reverse('ballot'), self.vote_data(self.ibrahim_voter, self.aisha))
        self.assertEqual(Ballot.objects.count(), 6)
        # Validate Ballot does not save anything
        voter = Voter.objects.get(student__first_name='Halima')
        president = Candidate.objects.get(student__first_name='Yusuf')
        self.client.post(reverse('ballot'), self.vote_data(voter, president, action='validate'))
        self.assertEqual(Ballot.objects.count(), 6)

    def test_no_voting_when_election_is_not_ongoing(self):
        self.election.end_election()
        voter = Voter.objects.get(student__first_name='Halima')
        president = Candidate.objects.get(student__first_name='Yusuf')
        ok, message = voter.vote(president)
        self.assertFalse(ok)
        self.assertEqual(Ballot.objects.count(), 5)

    def test_start_and_end_election_buttons(self):
        self.login('staff1')
        pending = Election.objects.get(title='Faculty Representatives 2026')
        self.client.post(reverse('election_start', args=[pending.pk]))
        pending.refresh_from_db()
        self.assertEqual(pending.status, 'Ongoing')
        self.client.post(reverse('election_end', args=[pending.pk]))
        pending.refresh_from_db()
        self.assertEqual(pending.status, 'Ended')

    def test_results_count_votes(self):
        self.login('user1')
        response = self.client.get(reverse('results'))
        self.assertContains(response, 'Aisha Nakato')
