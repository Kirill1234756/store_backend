# Generated by Django 5.0.4 on 2025-04-10 21:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=255)),
                ('method', models.CharField(max_length=10)),
                ('status_code', models.IntegerField()),
                ('response_time', models.FloatField(help_text='Response time in seconds')),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
                'indexes': [models.Index(fields=['-timestamp'], name='monitoring__timesta_2473aa_idx'), models.Index(fields=['path'], name='monitoring__path_e6b9f2_idx')],
            },
        ),
    ]
