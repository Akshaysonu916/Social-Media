# Generated by Django 5.2.1 on 2025-06-15 13:15

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0015_remove_follow_is_accepted'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('event_type', models.CharField(choices=[('Conference', 'Conference'), ('Workshop', 'Workshop'), ('Networking', 'Networking'), ('Social', 'Social Gathering'), ('Other', 'Other')], max_length=20)),
                ('date', models.DateTimeField()),
                ('location', models.CharField(max_length=200)),
                ('image', models.ImageField(blank=True, null=True, upload_to='event_images/')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('featured', models.BooleanField(default=False)),
                ('creator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
