# Generated by Django 4.1.2 on 2022-11-23 13:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("AdminSpace", "0009_alter_election_electioncandidates"),
    ]

    operations = [
        migrations.AlterField(
            model_name="election",
            name="ElectionCandidates",
            field=models.CharField(blank=True, max_length=10000, null=True),
        ),
    ]