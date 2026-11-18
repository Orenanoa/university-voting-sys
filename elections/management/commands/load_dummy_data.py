from django.core.management.base import BaseCommand

from elections.models import Ballot, Candidate, Election, Position, Student, Voter


class Command(BaseCommand):
    help = 'Load five rows of dummy data for each model'

    def handle(self, *args, **options):
        students = []
        for sid, first, last, gender, course, year, session in [
            ('S001', 'Aisha', 'Nakato', 'Female', 'Computer Science', 3, 'Day'),
            ('S002', 'Ibrahim', 'Mugisha', 'Male', 'Business Administration', 2, 'Evening'),
            ('S003', 'Maryam', 'Namukasa', 'Female', 'Education', 4, 'Day'),
            ('S004', 'Yusuf', 'Kiggundu', 'Male', 'Law', 1, 'Weekend'),
            ('S005', 'Halima', 'Nabirye', 'Female', 'Information Technology', 3, 'Day'),
        ]:
            student, _ = Student.objects.get_or_create(student_id=sid, defaults={
                'first_name': first, 'last_name': last, 'student_gender': gender,
                'course': course, 'year_of_study': year, 'session': session})
            students.append(student)

        elections = []
        for title, status in [('Guild Elections 2026', 'Ongoing'), ('Faculty Representatives 2026', 'Pending'),
                              ('Hall Council 2025', 'Ended'), ("Freshers' Representatives 2026", 'Pending'),
                              ('Sports Council 2025', 'Ended')]:
            election, _ = Election.objects.get_or_create(title=title, defaults={'status': status})
            elections.append(election)
        guild = elections[0]

        positions = []
        for election, title, description in [
            (guild, 'Guild President', 'Leads the student guild and represents students to management.'),
            (guild, 'Vice President', 'Deputises the President and coordinates guild committees.'),
            (guild, 'General Secretary', 'Keeps guild records and minutes of meetings.'),
            (guild, 'Finance Secretary', 'Manages the guild budget and accounts.'),
            (elections[2], 'Hall Chairperson', "Leads the hall council and handles residents' concerns."),
        ]:
            position, _ = Position.objects.get_or_create(election=election, title=title,
                                                         defaults={'description': description})
            positions.append(position)

        # (student, age, position)
        voters = []
        for student, age, position in [(students[0], 21, positions[0]), (students[1], 20, positions[2]),
                                       (students[2], 23, positions[2]), (students[3], 19, positions[0]),
                                       (students[4], 22, positions[3])]:
            voter, _ = Voter.objects.get_or_create(election=guild, student=student,
                                                   defaults={'voter_age': age, 'position': position})
            voters.append(voter)

        # (student, position, voter)
        candidates = []
        for student, position, voter in [(students[0], positions[0], voters[0]), (students[3], positions[0], voters[3]),
                                         (students[2], positions[2], voters[2]), (students[1], positions[2], voters[1]),
                                         (students[4], positions[3], voters[4])]:
            candidate, _ = Candidate.objects.get_or_create(student=student, candidate_position=position,
                                                           defaults={'candidate_voter': voter, 'status': 'Approved'})
            candidates.append(candidate)

        # (voter, candidate)
        for voter, candidate in [(voters[0], candidates[0]), (voters[1], candidates[2]), (voters[2], candidates[3]),
                                 (voters[3], candidates[1]), (voters[4], candidates[4])]:
            Ballot.objects.get_or_create(voter=voter, election=guild,
                                         position=candidate.candidate_position, candidate=candidate)

        self.stdout.write(self.style.SUCCESS('Dummy data loaded: 5 rows for each model.'))
