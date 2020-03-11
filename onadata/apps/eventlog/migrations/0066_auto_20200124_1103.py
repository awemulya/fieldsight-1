# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('eventlog', '0065_auto_20200116_1307'),
    ]

    operations = [
        migrations.AlterField(
            model_name='fieldsightlog',
            name='type',
            field=models.IntegerField(default=0, choices=[(1, 'User was added as the Team Admin of Organization Name by Invitor Full Name.'), (2, 'User was added as the Project Manager of Project Name by Invitor Full Name.'), (3, 'User was added as Reviewer of Site Name by Invitor Full Name.'), (4, 'User was added as Site Supervisor of Site Name by Invitor Full Name.'), (5, 'User was assigned as an Team Admin in Organization Name.'), (6, 'User was assigned as a Project Manager in Project Name.'), (7, 'User was assigned as a Reviewer in Site Name.'), (8, 'User was assigned as a Site Supervisor in Site Name.'), (9, 'User created a new Team named Organization Name'), (10, 'User created a new project named Project Name.'), (11, 'User created a new site named Site Name in Project Name.'), (110, 'User created a new Sub site named Site Name in Site Name.'), (12, 'User created number + sites in Project Name.'), (13, 'User changed the details of Organization Name.'), (14, 'User changed the details of Project Name.'), (15, 'User changed the details of Site Name.'), (16, 'User submitted a response for Form Type Form Name in Site Name.'), (17, 'User reviewed a response for Form Type Form Name in Site Name.'), (18, 'User assigned a new Form Type Form Name in Project Name.'), (19, 'User assigned a new Form Type Form Name to Site Name.'), (20, 'User edited Form Name form.'), (21, 'User assign successful in Team.'), (22, 'User assign sucessfull in project.'), (23, 'Users were already assigned.'), (24, 'User was added as unassigned.'), (25, 'User was added as partner in project.'), (26, 'User was added as the Project Manager in count project of org by Invitor Full Name.'), (27, 'User was added as Reviewer in count site of project by Invitor Full Name.'), (28, 'User was added as Site Supervisor in count site of project by Invitor Full Name.'), (29, 'Project SIte Import From Project Name Completed SuccessFully'), (30, 'Project SIte Import From number of region in Project Name Completed SuccessFully'), (31, 'User edited a response for Form Type Form Name in Site Name.'), (32, 'Report generated sucessfull.'), (33, 'Response Delete sucessfull.'), (34, 'Delete form sucessful.'), (341, 'Delete stages sucessful.'), (343, 'Delete substages sucessful.'), (342, 'Delete stage sucessful.'), (35, 'Remove roles.'), (36, 'Delete project/site/org/ .. etc.'), (37, 'User was added as Region Reviewer of Region Name by Invitor Full Name.'), (38, 'User was added as Region Supervisor of Region Name by Invitor Full Name.'), (39, 'User was added as Region Reviewer in count regions of project by Invitor Full Name.'), (40, 'User was added as Region Supervisor in count regions of project by Invitor Full Name.'), (41, 'User was added as the Super Organization Admin of Organization Name by Invitor Full Name.'), (412, 'Bulk upload of number + sites in Project Name failed.'), (421, 'User assign unsuccessful in Team.'), (422, 'User assign unsucessfull in project.'), (429, 'Project SIte Import From Project Name Completed SuccessFully'), (430, 'Project SIte Import From number of region in Project Name Completed SuccessFully'), (432, 'Report generation failed.'), (42, 'User was added as Team Admin in count teams of organization by Invitor Full Name.')]),
        ),
    ]
