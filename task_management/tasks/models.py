from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver

# We extend AbstractUser to support custom roles and auth.
class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Project Manager', 'Project Manager'),
        ('Team Member', 'Team Member'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='Team Member')

    def is_admin(self):
        return self.role == 'Admin'

    def is_manager(self):
        return self.role == 'Project Manager'

    def is_member(self):
        return self.role == 'Team Member'

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    profile_image = models.FileField(upload_to='profiles/', blank=True, null=True)

    def __str__(self):
        return self.full_name or self.user.username

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(
            user=instance, 
            email=instance.email or '', 
            full_name=f"{instance.first_name} {instance.last_name}".strip() or instance.username
        )

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class Project(models.Model):
    STATUS_CHOICES = (
        ('Planning', 'Planning'),
        ('Active', 'Active'),
        ('On Hold', 'On Hold'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Planning')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    members = models.ManyToManyField(User, related_name='projects', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Task(models.Model):
    PRIORITY_CHOICES = (
        ('Low', 'Low'),
        ('Medium', 'Medium'),
        ('High', 'High'),
        ('Critical', 'Critical'),
    )
    STATUS_CHOICES = (
        ('To Do', 'To Do'),
        ('In Progress', 'In Progress'),
        ('Review', 'Review'),
        ('Done', 'Done'),
        ('Blocked', 'Blocked'),
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    start_date = models.DateField()
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='To Do')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')

    def __str__(self):
        return f"Comment by {self.author.username} on {self.task.title}"

class Attachment(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='attachments')
    file = models.FileField(upload_to='attachments/')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attachments')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.file.name} by {self.uploaded_by.username}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}: {self.message[:50]}"
