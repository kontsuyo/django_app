from django.urls import path

from sns import views

urlpatterns = [
    path("", views.index, name="index"),
    path("<int:page>", views.index, name="index"),
    path("groups", views.groups, name="groups"),
    path("add", views.add, name="add"),
    path("create_group", views.create_group, name="create_group"),
    path("post", views.post, name="post"),
    path("share/<int:share_id>", views.share, name="share"),
    path("good/<int:good_id>", views.good, name="good"),
]
