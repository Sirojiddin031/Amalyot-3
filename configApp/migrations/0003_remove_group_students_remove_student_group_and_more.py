# Generated by Django 5.1.7 on 2025-03-15 01:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('configApp', '0002_alter_user_email'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='group',
            name='students',
        ),
        migrations.RemoveField(
            model_name='student',
            name='group',
        ),
        migrations.RemoveField(
            model_name='user',
            name='created_at',
        ),
        migrations.AddField(
            model_name='student',
            name='groups',
            field=models.ManyToManyField(blank=True, related_name='students', to='configApp.group'),
        ),
        migrations.AlterField(
            model_name='group',
            name='teacher',
            field=models.ManyToManyField(related_name='teacher_groups', to='configApp.worker'),
        ),
        migrations.AlterField(
            model_name='student',
            name='course',
            field=models.ManyToManyField(blank=True, related_name='students', to='configApp.course'),
        ),
        migrations.AlterField(
            model_name='worker',
            name='course',
            field=models.ManyToManyField(related_name='workers', to='configApp.course'),
        ),
        migrations.AlterField(
            model_name='worker',
            name='departments',
            field=models.ManyToManyField(related_name='workers', to='configApp.departments'),
        ),
    ]
