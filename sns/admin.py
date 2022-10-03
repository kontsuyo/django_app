from django.contrib import admin

from sns.models import Friend
from sns.models import Good
from sns.models import Group
from sns.models import Message

admin.site.register(Message)
admin.site.register(Group)
admin.site.register(Friend)
admin.site.register(Good)
