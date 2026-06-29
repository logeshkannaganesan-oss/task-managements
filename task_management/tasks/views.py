from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from .models import User, Profile, Project, Task, Comment, Attachment, Notification
from .forms import (
    UserRegisterForm, UserProfileForm, ProjectForm, TaskForm, 
    TaskStatusForm, CommentForm, AttachmentForm
)

# Helper functions to check roles
def is_admin(user):
    return user.is_authenticated and user.role == 'Admin'

def is_manager(user):
    return user.is_authenticated and user.role in ['Project Manager', 'Admin']

# Base/Redirect view
def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    if request.user.role == 'Admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'Project Manager':
        return redirect('manager_dashboard')
    else:
        return redirect('member_dashboard')

# User Authentication
def register_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registration successful. You can now login.")
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'tasks/register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('index')
    if request.method == 'POST':
        username = request.POST.get('username')
        passw = request.POST.get('password')
        user = authenticate(request, username=username, password=passw)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('index')
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, 'tasks/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')

# Profile Views
@login_required
def profile_view(request, username=None):
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    profile = get_object_or_404(Profile, user=user)
    
    # Only the owner or Admin can edit the profile
    can_edit = (request.user == user or request.user.role == 'Admin')
    
    if request.method == 'POST' and can_edit:
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            # Also sync profile email back to User if changed
            email = form.cleaned_data.get('email')
            if email and email != user.email:
                user.email = email
                user.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile', username=user.username)
    else:
        form = UserProfileForm(instance=profile)
        
    return render(request, 'tasks/profile.html', {
        'profile_user': user,
        'profile': profile,
        'form': form,
        'can_edit': can_edit
    })

# Dashboards
@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("Admin access required.")
    
    users = User.objects.all()
    projects = Project.objects.all()
    tasks = Task.objects.all()
    
    context = {
        'total_users': users.count(),
        'total_projects': projects.count(),
        'total_tasks': tasks.count(),
        'users_list': users,
        'projects_list': projects,
    }
    return render(request, 'tasks/admin_dashboard.html', context)

@login_required
def manager_dashboard(request):
    if not is_manager(request.user):
        return HttpResponseForbidden("Manager access required.")
        
    # Projects created by the manager or where they are assigned/member
    projects = Project.objects.filter(Q(created_by=request.user) | Q(members=request.user)).distinct()
    
    # All team members (excluding admins)
    team_members = User.objects.filter(role='Team Member')
    
    # Pending tasks in projects managed by this user
    pending_tasks = Task.objects.filter(project__in=projects).exclude(status='Done')
    
    context = {
        'projects': projects,
        'team_members': team_members,
        'pending_tasks': pending_tasks,
    }
    return render(request, 'tasks/manager_dashboard.html', context)

@login_required
def member_dashboard(request):
    # Assigned tasks
    assigned_tasks = Task.objects.filter(assigned_user=request.user)
    
    # Tasks nearing deadlines (excluding Done, sorted by due_date)
    deadlines = assigned_tasks.exclude(status='Done').order_on_due_dates = assigned_tasks.exclude(status='Done').order_by('due_date')
    
    # Unread notifications
    notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')
    
    context = {
        'assigned_tasks': assigned_tasks,
        'deadlines': deadlines,
        'notifications': notifications,
    }
    return render(request, 'tasks/member_dashboard.html', context)

# Admin User Management CRUD
@login_required
def admin_user_create(request):
    if not is_admin(request.user):
        return HttpResponseForbidden("Admin access required.")
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect('admin_dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'tasks/user_form.html', {'form': form, 'action': 'Create'})

@login_required
def admin_user_edit(request, user_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("Admin access required.")
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)
    if request.method == 'POST':
        # Admin can update user role, username, email
        user.username = request.POST.get('username')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.role = request.POST.get('role')
        user.email = request.POST.get('email')
        user.save()
        
        # Profile fields
        profile.full_name = f"{user.first_name} {user.last_name}".strip()
        profile.email = user.email
        profile.department = request.POST.get('department', '')
        profile.designation = request.POST.get('designation', '')
        profile.phone_number = request.POST.get('phone_number', '')
        if 'profile_image' in request.FILES:
            profile.profile_image = request.FILES['profile_image']
        profile.save()
        
        messages.success(request, "User and profile updated successfully.")
        return redirect('admin_dashboard')
    
    return render(request, 'tasks/user_form.html', {
        'edit_user': user,
        'profile': profile,
        'action': 'Edit'
    })

@login_required
def admin_user_delete(request, user_id):
    if not is_admin(request.user):
        return HttpResponseForbidden("Admin access required.")
    user = get_object_or_404(User, id=user_id)
    if user == request.user:
        messages.error(request, "You cannot delete your own account.")
    else:
        user.delete()
        messages.success(request, "User deleted successfully.")
    return redirect('admin_dashboard')

# Project CRUD
@login_required
def project_create(request):
    if not is_manager(request.user):
        return HttpResponseForbidden("Only Managers and Admins can create projects.")
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.save()
            form.save_m2m() # Save members
            messages.success(request, "Project created successfully.")
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm()
    return render(request, 'tasks/project_form.html', {'form': form, 'action': 'Create'})

@login_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Check permissions (only creator, members, or Admin can view details)
    if not (request.user.role == 'Admin' or project.created_by == request.user or request.user in project.members.all()):
        return HttpResponseForbidden("You are not authorized to view this project.")
        
    tasks = project.tasks.all()
    attachments = project.attachments.all()
    attachment_form = AttachmentForm()
    
    context = {
        'project': project,
        'tasks': tasks,
        'attachments': attachments,
        'attachment_form': attachment_form
    }
    return render(request, 'tasks/project_detail.html', context)

@login_required
def project_edit(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not (is_admin(request.user) or project.created_by == request.user):
        return HttpResponseForbidden("Only the project creator or Admin can edit this project.")
        
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully.")
            return redirect('project_detail', project_id=project.id)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'tasks/project_form.html', {'form': form, 'action': 'Edit', 'project': project})

@login_required
def project_delete(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    if not (is_admin(request.user) or project.created_by == request.user):
        return HttpResponseForbidden("Only the project creator or Admin can delete this project.")
        
    if request.method == 'POST':
        project.delete()
        messages.success(request, "Project deleted successfully.")
        return redirect('index')
        
    return render(request, 'tasks/project_confirm_delete.html', {'project': project})

# Task CRUD
@login_required
def task_create(request, project_id=None):
    if not is_manager(request.user):
        return HttpResponseForbidden("Only Managers and Admins can create tasks.")
        
    project = None
    if project_id:
        project = get_object_or_404(Project, id=project_id)
        
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save()
            # Send Notification to assigned user
            if task.assigned_user:
                Notification.objects.create(
                    user=task.assigned_user,
                    message=f"You have been assigned a new task: '{task.title}' in project '{task.project.name}'"
                )
            messages.success(request, "Task created successfully.")
            return redirect('project_detail', project_id=task.project.id)
    else:
        if project:
            form = TaskForm(initial={'project': project})
        else:
            # Limit projects list to those managed by this user (or all if admin)
            if request.user.role == 'Admin':
                project_qs = Project.objects.all()
            else:
                project_qs = Project.objects.filter(Q(created_by=request.user) | Q(members=request.user)).distinct()
            form = TaskForm(project_qs=project_qs)
            
    return render(request, 'tasks/task_form.html', {'form': form, 'action': 'Create', 'project': project})

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    
    # Check project membership or admin status
    if not (request.user.role == 'Admin' or project.created_by == request.user or request.user in project.members.all()):
        return HttpResponseForbidden("You are not authorized to view this task.")
        
    comments = task.comments.filter(parent=None).prefetch_related('replies')
    attachments = task.attachments.all()
    
    comment_form = CommentForm()
    attachment_form = AttachmentForm()
    
    # Provide simple status edit option directly on the detail page or via status form
    status_form = TaskStatusForm(instance=task)
    
    context = {
        'task': task,
        'comments': comments,
        'attachments': attachments,
        'comment_form': comment_form,
        'attachment_form': attachment_form,
        'status_form': status_form
    }
    return render(request, 'tasks/task_detail.html', context)

@login_required
def task_edit(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    
    # Managers/Admins can edit everything. Assignees can only edit status.
    is_mgr = is_admin(request.user) or project.created_by == request.user
    is_assignee = task.assigned_user == request.user
    
    if not (is_mgr or is_assignee):
        return HttpResponseForbidden("You are not authorized to edit this task.")
        
    if request.method == 'POST':
        if is_mgr:
            form = TaskForm(request.POST, instance=task)
        else:
            form = TaskStatusForm(request.POST, instance=task)
            
        if form.is_valid():
            updated_task = form.save()
            # Send Notification on updates
            if is_assignee and not is_mgr:
                # Notify manager/creator
                Notification.objects.create(
                    user=project.created_by,
                    message=f"Team member {request.user.username} updated status of task '{task.title}' to '{task.status}'"
                )
            elif is_mgr and updated_task.assigned_user:
                Notification.objects.create(
                    user=updated_task.assigned_user,
                    message=f"Task '{task.title}' details have been updated by a manager."
                )
                
            messages.success(request, "Task updated successfully.")
            return redirect('task_detail', task_id=task.id)
    else:
        if is_mgr:
            form = TaskForm(instance=task)
        else:
            form = TaskStatusForm(instance=task)
            
    return render(request, 'tasks/task_form.html', {
        'form': form,
        'action': 'Edit',
        'task': task,
        'status_only': not is_mgr
    })

@login_required
def task_delete(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    project = task.project
    if not (is_admin(request.user) or project.created_by == request.user):
        return HttpResponseForbidden("Only Managers and Admins can delete tasks.")
        
    if request.method == 'POST':
        proj_id = task.project.id
        task.delete()
        messages.success(request, "Task deleted successfully.")
        return redirect('project_detail', project_id=proj_id)
        
    return render(request, 'tasks/task_confirm_delete.html', {'task': task})

# Comments and Replies
@login_required
def add_comment(request, task_id):
    task = get_object_or_404(Task, id=task_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.task = task
            comment.author = request.user
            
            parent_id = request.POST.get('parent_id')
            if parent_id:
                parent_comment = get_object_or_404(Comment, id=parent_id)
                comment.parent = parent_comment
                # Notify parent comment author if they aren't the replier
                if parent_comment.author != request.user:
                    Notification.objects.create(
                        user=parent_comment.author,
                        message=f"{request.user.username} replied to your comment on task '{task.title}'"
                    )
            else:
                # Notify assignee
                if task.assigned_user and task.assigned_user != request.user:
                    Notification.objects.create(
                        user=task.assigned_user,
                        message=f"{request.user.username} commented on your task '{task.title}'"
                    )
                    
            comment.save()
            messages.success(request, "Comment posted.")
    return redirect('task_detail', task_id=task.id)

# File Upload Module
@login_required
def upload_attachment(request):
    if request.method == 'POST':
        form = AttachmentForm(request.POST, request.FILES)
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.uploaded_by = request.user
            
            project_id = request.POST.get('project_id')
            task_id = request.POST.get('task_id')
            
            if project_id:
                project = get_object_or_404(Project, id=project_id)
                attachment.project = project
                attachment.save()
                messages.success(request, "Attachment uploaded to project.")
                return redirect('project_detail', project_id=project.id)
            elif task_id:
                task = get_object_or_404(Task, id=task_id)
                attachment.task = task
                attachment.save()
                messages.success(request, "Attachment uploaded to task.")
                return redirect('task_detail', task_id=task.id)
                
    messages.error(request, "Failed to upload attachment.")
    return redirect('index')

# Search & Filter
@login_required
def search_results(request):
    q = request.GET.get('q', '')
    status_filter = request.GET.get('status', '')
    priority_filter = request.GET.get('priority', '')
    assignee_filter = request.GET.get('assignee', '')
    
    projects = Project.objects.all()
    tasks = Task.objects.all()
    users = User.objects.all()
    
    # Role-based restriction: managers/members see their projects/tasks
    if request.user.role != 'Admin':
        projects = projects.filter(Q(created_by=request.user) | Q(members=request.user)).distinct()
        tasks = tasks.filter(project__in=projects)
        
    if q:
        projects = projects.filter(name__icontains=q)
        tasks = tasks.filter(Q(title__icontains=q) | Q(description__icontains=q))
        users = users.filter(Q(username__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q))
        
    if status_filter:
        projects = projects.filter(status=status_filter)
        tasks = tasks.filter(status=status_filter)
        
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)
        
    if assignee_filter:
        tasks = tasks.filter(assigned_user_id=assignee_filter)
        
    all_users = User.objects.exclude(role='Admin')
    project_statuses = Project.STATUS_CHOICES
    task_statuses = Task.STATUS_CHOICES
    priority_choices = Task.PRIORITY_CHOICES
    
    context = {
        'q': q,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'assignee_filter': assignee_filter,
        'projects': projects,
        'tasks': tasks,
        'users': users,
        'all_users': all_users,
        'project_statuses': project_statuses,
        'task_statuses': task_statuses,
        'priority_choices': priority_choices,
    }
    return render(request, 'tasks/search_results.html', context)

# Notification Manager
@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    return redirect('member_dashboard')

# Report Module
@login_required
def reports_view(request):
    # Only Admin or Manager can view reports
    if not is_manager(request.user):
        return HttpResponseForbidden("You are not authorized to view reports.")
        
    # Project Completion Report
    all_projects = Project.objects.all()
    project_count = all_projects.count()
    completed_projects_count = all_projects.filter(status='Completed').count()
    project_completion_rate = round((completed_projects_count / project_count * 100), 2) if project_count > 0 else 0
    remaining_completion_rate = 100 - project_completion_rate
    
    # Task Status Report
    all_tasks = Task.objects.all()
    task_status_data = all_tasks.values('status').annotate(count=Count('id'))
    
    # User Productivity Report
    users_data = User.objects.exclude(role='Admin').annotate(
        assigned_tasks_count=Count('assigned_tasks', distinct=True),
        completed_tasks_count=Count('assigned_tasks', filter=Q(assigned_tasks__status='Done'), distinct=True),
        comments_count=Count('comments', distinct=True)
    )
    
    context = {
        'all_projects': all_projects,
        'project_completion_rate': project_completion_rate,
        'remaining_completion_rate': remaining_completion_rate,
        'completed_projects_count': completed_projects_count,
        'project_count': project_count,
        'task_status_data': task_status_data,
        'users_data': users_data,
    }
    return render(request, 'tasks/reports.html', context)
