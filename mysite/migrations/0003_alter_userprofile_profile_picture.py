# Generated by Django 5.1.6 on 2025-04-29 16:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mysite', '0002_alter_userprofile_profile_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='profile_picture',
            field=models.ImageField(blank=True, default='/static/default_avatar.png', null=True, upload_to='profiles/'),
        ),
    ]
