from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Candidate, Election, Position
from .pages import PAGES


# ---------- helpers ----------

def staff_only(view):
    """Only logged-in staff users may use this view."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(request, 'Only staff members can do that.')
            return redirect('home')
        return view(request, *args, **kwargs)
    return wrapper


def get_value(obj, path):
    """Read 'student.full_name' style values from an object (calls methods)."""
    value = obj
    for part in path.split('.'):
        value = getattr(value, part)
        if callable(value):
            value = value()
    return value


def row_actions(request, name, obj):
    """Buttons shown at the end of each table row."""
    actions = []
    if name == 'election':
        actions.append({'label': 'Candidates', 'css': 'blue', 'url': reverse('election_candidates', args=[obj.pk])})
        if request.user.is_staff:
            actions.append({'label': 'Start', 'css': 'green', 'post': True, 'url': reverse('election_start', args=[obj.pk])})
            actions.append({'label': 'End', 'css': 'red', 'post': True, 'url': reverse('election_end', args=[obj.pk])})
    if name == 'position':
        actions.append({'label': 'Candidates', 'css': 'blue', 'url': reverse('position_candidates', args=[obj.pk])})
        if request.user.is_staff:
            actions.append({'label': 'Add Candidate', 'css': 'green',
                            'url': reverse('candidate') + f'?candidate_position={obj.pk}'})
    if name == 'candidate':
        actions.append({'label': 'Information', 'css': 'blue', 'url': reverse('candidate_info', args=[obj.pk])})
    if name == 'voter':
        actions.append({'label': 'Vote', 'css': 'green',
                        'url': reverse('ballot') + f'?voter={obj.pk}&election={obj.election_id}&position={obj.position_id}'})
    if request.user.is_staff:
        actions.append({'label': 'Edit', 'css': 'dark', 'url': reverse(f'{name}_edit', args=[obj.pk])})
        actions.append({'label': 'Delete', 'css': 'red', 'url': reverse(f'{name}_delete', args=[obj.pk])})
    return actions


def table_context(request, name, objects):
    """Turn a list of records into headers + rows for table.html."""
    page = PAGES[name]
    rows = []
    for obj in objects:
        cells = [get_value(obj, attr) for header, attr in page['columns']]
        rows.append({'cells': cells, 'actions': row_actions(request, name, obj)})
    headers = [header for header, attr in page['columns']]
    return {'headers': headers, 'rows': rows, 'colspan': len(headers) + 1,
            'show_actions': any(row['actions'] for row in rows)}


# ---------- authentication ----------

class LoginPage(LoginView):
    template_name = 'registration/login.html'

    def form_valid(self, form):
        messages.success(self.request, f'Login successful. Welcome, {form.get_user().username}!')
        return super().form_valid(form)


def register(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Account created. You can log in now.')
        return redirect('login')
    return render(request, 'registration/register.html', {'form': form})


# ---------- home ----------

@login_required
def home(request):
    return render(request, 'home.html')


# ---------- CRUD for every object ----------

@login_required
def object_list(request, name):
    """Read + Create: the form on top, the table below."""
    page = PAGES[name]
    can_add = request.user.is_staff or page.get('open_to_all', False)
    form = None
    if can_add:
        form = page['form'](request.POST or None, initial=request.GET.dict())
        if request.method == 'POST' and form.is_valid():
            if request.POST.get('action') == 'validate':
                messages.success(request, 'Ballot is valid and ready to submit.')
            else:
                form.save()
                messages.success(request, page.get('saved_message', page['title'] + ' saved successfully.'))
                return redirect(name)
    context = table_context(request, name, page['model'].objects.all())
    context.update({'page': page, 'name': name, 'form': form})
    return render(request, 'object_page.html', context)


@staff_only
def object_edit(request, name, pk):
    """Update."""
    page = PAGES[name]
    obj = get_object_or_404(page['model'], pk=pk)
    form = page['form'](request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, page['title'] + ' updated successfully.')
        return redirect(name)
    return render(request, 'object_edit.html', {'page': page, 'name': name, 'form': form})


@staff_only
def object_delete(request, name, pk):
    """Delete (asks for confirmation first)."""
    page = PAGES[name]
    obj = get_object_or_404(page['model'], pk=pk)
    if request.method == 'POST':
        obj.delete()
        messages.success(request, page['title'] + ' deleted successfully.')
        return redirect(name)
    return render(request, 'object_delete.html', {'page': page, 'name': name, 'object': obj})


# ---------- election buttons ----------

@require_POST
@staff_only
def election_start(request, pk):
    election = get_object_or_404(Election, pk=pk)
    election.start_election()
    messages.success(request, f'Election "{election.title}" started.')
    return redirect('election')


@require_POST
@staff_only
def election_end(request, pk):
    election = get_object_or_404(Election, pk=pk)
    election.end_election()
    messages.success(request, f'Election "{election.title}" ended.')
    return redirect('election')


@login_required
def election_candidates(request, pk):
    election = get_object_or_404(Election, pk=pk)
    context = table_context(request, 'candidate', election.display_candidates())
    context.update({'heading': f'Candidates: {election.title}',
                    'lead': 'Everyone standing in this election.', 'back': 'election'})
    return render(request, 'table_page.html', context)


@login_required
def position_candidates(request, pk):
    position = get_object_or_404(Position, pk=pk)
    context = table_context(request, 'candidate', position.display_candidates())
    context.update({'heading': f'Candidates: {position.title}',
                    'lead': f'Everyone standing for {position.title} in {position.election}.', 'back': 'position'})
    return render(request, 'table_page.html', context)


@login_required
def candidate_info(request, pk):
    candidate = get_object_or_404(Candidate, pk=pk)
    rows = [{'cells': [candidate.candidate_id, candidate.student.full_name(),
                       candidate.candidate_position, candidate.status, candidate.votes()], 'actions': []}]
    context = {'heading': 'Candidate Information', 'lead': candidate.display_information(),
               'headers': ['Candidate ID', 'Student', 'Position', 'Status', 'Votes received'],
               'rows': rows, 'show_actions': False, 'colspan': 5, 'back': 'candidate'}
    return render(request, 'table_page.html', context)


# ---------- results ----------

@login_required
def results(request):
    candidates = (Candidate.objects.select_related('student', 'candidate_position__election')
                  .annotate(total=Count('ballots'))
                  .order_by('candidate_position__election__title', 'candidate_position__title', '-total'))
    rows = [{'cells': [c.candidate_position.election, c.candidate_position, c.student.full_name(), c.total],
             'actions': []} for c in candidates]
    context = {'heading': 'Results', 'lead': 'Votes received by each candidate.',
               'headers': ['Election', 'Position', 'Candidate', 'Votes'],
               'rows': rows, 'show_actions': False, 'colspan': 4}
    return render(request, 'table_page.html', context)
