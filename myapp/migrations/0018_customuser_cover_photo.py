# Generated by Django 5.2.1 on 2025-06-22 07:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0017_customuser_is_public'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='cover_photo',
            field=models.ImageField(blank=True, null=True, upload_to='cover_photos/'),
        ),
    ]
