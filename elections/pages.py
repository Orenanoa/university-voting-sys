"""One entry per object page. The views read this dictionary, so every page
(Student, Election, Position, Candidate, Voter, Ballot) works the same way."""
from .forms import BallotForm, CandidateForm, ElectionForm, PositionForm, StudentForm, VoterForm
from .models import Ballot, Candidate, Election, Position, Student, Voter

PAGES = {
    'students': {
        'model': Student, 'form': StudentForm, 'title': 'Student',
        'heading': 'Register Student', 'lead': 'Add a student to the register.',
        'save_label': 'Register', 'table_title': 'Registered Students',
        'columns': [('Student ID', 'student_id'), ('First Name', 'first_name'), ('Last Name', 'last_name'),
                    ('Gender', 'student_gender'), ('Course', 'course'),
                    ('Year of Study', 'year_of_study'), ('Session', 'session')],
    },
    'election': {
        'model': Election, 'form': ElectionForm, 'title': 'Election',
        'heading': 'Election', 'lead': 'Create an election, start it, and close it when voting ends.',
        'save_label': 'Save', 'table_title': 'Elections',
        'columns': [('Election ID', 'election_id'), ('Title', 'title'),
                    ('Voters (registered)', 'voters'), ('Status', 'status')],
    },
    'position': {
        'model': Position, 'form': PositionForm, 'title': 'Position',
        'heading': 'Position', 'lead': 'Define the positions students can stand for in an election.',
        'save_label': 'Save Position', 'table_title': 'Positions',
        'columns': [('Position ID', 'position_id'), ('Election', 'election'),
                    ('Title', 'title'), ('Description', 'description')],
    },
    'candidate': {
        'model': Candidate, 'form': CandidateForm, 'title': 'Candidate',
        'heading': 'Candidate', 'lead': 'Register students as candidates for a position.',
        'save_label': 'Save Candidate', 'table_title': 'Registered Candidates',
        'columns': [('Candidate ID', 'candidate_id'), ('Student', 'student.full_name'),
                    ('Candidate Position', 'candidate_position'),
                    ('Candidate Voter', 'candidate_voter.voter_id'), ('Status', 'status')],
    },
    'voter': {
        'model': Voter, 'form': VoterForm, 'title': 'Voter',
        'heading': 'Voter', 'lead': 'Register a student as a voter in an election.',
        'save_label': 'Register', 'table_title': 'Registered Voters',
        'extra_buttons': [{'label': 'Vote', 'url_name': 'ballot', 'css': 'green'}],
        'columns': [('Voter ID', 'voter_id'), ('Election', 'election'), ('Student', 'student.full_name'),
                    ('Voter Age', 'voter_age'), ('Position', 'position')],
    },
    'ballot': {
        'model': Ballot, 'form': BallotForm, 'title': 'Ballot',
        'heading': 'Ballot', 'lead': 'Choose a candidate for a position, check the ballot, then submit it.',
        'save_label': 'Submit Ballot', 'table_title': 'Submitted Ballots',
        'validate_button': True, 'open_to_all': True,
        'saved_message': 'Ballot submitted successfully. Thank you for voting.',
        'columns': [('Voter ID', 'voter_id'), ('Election', 'election'),
                    ('Position', 'position'), ('Candidate Name', 'candidate_name')],
    },
}
