from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import LoginView
from django.db.models import Count
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Candidate, Election, Position
from .pages import PAGES


# ---------- helpers ----------

def is_ajax(request):
    """True when the page's JavaScript (static/js/script.js) sent the request."""
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def can_edit(user):
    """Only admin (staff) users can add, edit and delete records.
    Set STAFF_ONLY_EDITING = False in settings.py to let every logged-in user do it."""
    return user.is_staff or not getattr(settings, 'STAFF_ONLY_EDITING', False)


def editor_only(view):
    """Only users who are allowed to edit may use this view."""
    @login_required
    def wrapper(request, *args, **kwargs):
        if not can_edit(request.user):
            if is_ajax(request):
                return JsonResponse({'ok': False, 'errors': ['Only the admin can do that.']}, status=403)
            messages.error(request, 'Only the admin can do that.')
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
        if can_edit(request.user):
            actions.append({'label': 'Start', 'css': 'green', 'post': True, 'url': reverse('election_start', args=[obj.pk])})
            actions.append({'label': 'End', 'css': 'red', 'post': True, 'url': reverse('election_end', args=[obj.pk])})
    if name == 'position':
        actions.append({'label': 'Candidates', 'css': 'blue', 'url': reverse('position_candidates', args=[obj.pk])})
        if can_edit(request.user):
            actions.append({'label': 'Add Candidate', 'css': 'green',
                            'url': reverse('candidate') + f'?candidate_position={obj.pk}'})
    if name == 'candidate':
        actions.append({'label': 'Information', 'css': 'blue', 'url': reverse('candidate_info', args=[obj.pk])})
    if name == 'voter':
        actions.append({'label': 'Vote', 'css': 'green',
                        'url': reverse('ballot') + f'?voter={obj.pk}&election={obj.election_id}&position={obj.position_id}'})
    if can_edit(request.user):
        actions.append({'label': 'Edit', 'css': 'dark', 'url': reverse(f'{name}_edit', args=[obj.pk])})
        # 'remove' = the page's JavaScript removes the row without leaving the page
        actions.append({'label': 'Remove', 'css': 'red', 'remove': True,
                        'url': reverse(f'{name}_delete', args=[obj.pk])})
    return actions


def has_actions_column(request, name):
    """Same answer for every row, so a table that starts empty still has an Actions column."""
    return can_edit(request.user) or name in ('election', 'position', 'candidate', 'voter')


def build_row(request, name, obj):
    page = PAGES[name]
    return {'cells': [get_value(obj, attr) for header, attr in page['columns']],
            'actions': row_actions(request, name, obj)}


def row_html(request, name, obj):
    """One finished <tr>, sent back to the page after a record is added."""
    return render_to_string('table_row.html', {
        'row': build_row(request, name, obj), 'show_actions': has_actions_column(request, name)}, request=request)


def table_context(request, name, objects):
    """Turn a list of records into headers + rows for table.html."""
    page = PAGES[name]
    rows = [build_row(request, name, obj) for obj in objects]
    headers = [header for header, attr in page['columns']]
    show_actions = has_actions_column(request, name)
    return {'headers': headers, 'rows': rows, 'show_actions': show_actions,
            'colspan': len(headers) + (1 if show_actions else 0)}


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
    """Read + Create: the form on top, the table below.
    The page's JavaScript posts the form in the background (AJAX): the new row is sent back
    and added to the table without reloading. Without JavaScript the normal redirect still works."""
    page = PAGES[name]
    ajax = is_ajax(request)
    can_add = can_edit(request.user) or page.get('open_to_all', False)
    if request.method == 'POST' and ajax and not can_add:
        return JsonResponse({'ok': False, 'errors': ['Only the admin can add records on this page.']}, status=403)
    form = None
    if can_add:
        form = page['form'](request.POST or None, initial=request.GET.dict())
        if request.method == 'POST' and form.is_valid():
            if request.POST.get('action') == 'validate':
                if ajax:
                    return JsonResponse({'ok': True, 'message': 'Ballot is valid and ready to submit.'})
                messages.success(request, 'Ballot is valid and ready to submit.')
            else:
                obj = form.save()
                message = page.get('saved_message', page['title'] + ' saved successfully.')
                if ajax:
                    return JsonResponse({'ok': True, 'message': message, 'row': row_html(request, name, obj)})
                messages.success(request, message)
                return redirect(name)
        elif request.method == 'POST' and ajax:
            errors = []
            for field, field_errors in form.errors.items():
                label = form.fields[field].label if field in form.fields else ''
                errors += [f'{label}: {e}' if label else str(e) for e in field_errors]
            return JsonResponse({'ok': False, 'errors': errors}, status=400)
    context = table_context(request, name, page['model'].objects.all())
    context.update({'page': page, 'name': name, 'form': form})
    return render(request, 'object_page.html', context)


@editor_only
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


@editor_only
def object_delete(request, name, pk):
    """Delete (asks for confirmation first)."""
    page = PAGES[name]
    obj = get_object_or_404(page['model'], pk=pk)
    if request.method == 'POST':
        obj.delete()
        if is_ajax(request):
            return JsonResponse({'ok': True, 'message': page['title'] + ' removed successfully.'})
        messages.success(request, page['title'] + ' deleted successfully.')
        return redirect(name)
    return render(request, 'object_delete.html', {'page': page, 'name': name, 'object': obj})


# ---------- election buttons ----------

@require_POST
@editor_only
def election_start(request, pk):
    election = get_object_or_404(Election, pk=pk)
    election.start_election()
    messages.success(request, f'Election "{election.title}" started.')
    return redirect('election')


@require_POST
@editor_only
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
