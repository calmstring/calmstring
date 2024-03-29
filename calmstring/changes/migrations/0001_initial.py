# Generated by Django 3.2 on 2022-06-11 15:38

import changes.models
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Change',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('name', models.CharField(blank=True, default='', max_length=200, null=True, verbose_name='Change name')),
                ('type', models.SlugField()),
                ('changes', models.JSONField(default=dict)),
                ('content_id', models.PositiveIntegerField(verbose_name='Object id')),
                ('object_uuid', models.UUIDField()),
                ('metadata', models.JSONField(default=changes.models.metadata_default_value)),
                ('author', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Change author')),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype', verbose_name='Object content type')),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='changes.change')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
