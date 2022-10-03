from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import redirect
from django.shortcuts import render

from sns.forms import CreateGroupForm
from sns.forms import FriendsForm
from sns.forms import GroupCheckBoxForm
from sns.forms import GroupSelectForm
from sns.forms import PostForm
from sns.models import Friend
from sns.models import Good
from sns.models import Group
from sns.models import Message


@login_required(login_url="/admin/login/")
def index(request, page=1):
    # publicのuserを取得
    (public_user, public_group) = get_public()

    # POST送信時の処理
    if request.method == "POST":
        # Groupsのチェックを更新したときの処理
        # フォームの処理
        group_check_box_form = GroupCheckBoxForm(request.user, request.POST)
        # チェックされたGroup名をリストにまとめる
        glist = []
        for group in request.POST.getlist("groups"):
            glist.append(group)
        # メッセージの取得
        message = get_your_group_message(request.user, glist, page)

    # GETアクセス時の処理
    if request.method != "POST":
        group_check_box_form = GroupCheckBoxForm(request.user)
        # Groupのリストを取得
        my_groups = Group.objects.filter(owner=request.user)
        glist = [public_group.title]
        for group in my_groups:
            glist.append(group.title)
        # メッセージの取得
        message = get_your_group_message(request.user, glist, page)

    # 共通処理
    params = {
        "login_user": request.user,
        "contents": message,
        "check_form": group_check_box_form,
    }
    return render(request, "sns/index.html", params)


@login_required(login_url="/admin/login")
def groups(request):
    # 自分が登録したFriendを取得
    friends = Friend.objects.filter(owner=request.user)

    # POST送信時の処理
    if request.method == "POST":

        # Groupsメニュー選択肢の処理
        if request.POST.get("mode") == "__groups_form__":
            # 選択したGroup名を取得
            sel_group = request.POST.get("groups")
            # Groupを取得
            gp = (
                Group.objects.filter(owner=request.user).filter(title=sel_group).first()
            )
            # Groupに含まれるFriendを取得
            fds = Friend.objects.filter(owner=request.user).filter(group=gp)
            print(Friend.objects.filter(owner=request.user))
            # FriendのUserをリストにまとめる
            vlist = []
            for item in fds:
                vlist.append(item.user.username)
            # フォームの用意
            groupsform = GroupSelectForm(request.user, request.POST)
            friendsform = FriendsForm(friends=friends, vals=vlist)

    # Friendsのチェック更新時の処理
    if request.POST.get("mode") == "__friends_form__":
        # 選択したGroupの取得
        sel_group = request.POST.get("group")
        group_obj = Group.objects.filter(title=sel_group).first()
        print(group_obj)
        # チェックしたFriendsを取得
        sel_fds = request.POST.getlist("friends")
        # FriendsのUserを取得
        sel_users = User.objects.filter(username__in=sel_fds)
        # Userのリストに含まれるユーザーが登録したFriendsを取得
        fds = Friend.objects.filter(owner=request.user).filter(user__in=sel_users)
        # すべてのFriendsにGroupを設定し保存する
        vlist = []
        for item in fds:
            item.group = group_obj
            item.save()
            vlist.append(item.user.username)
        # メッセージを設定
        messages.success(request, "チェックされたFriendを" + sel_group + "に登録しました。")
        # フォームの用意
        groupsform = GroupSelectForm(request.user, {"groups": sel_group})
        friendsform = FriendsForm(friends=friends, vals=vlist)

    # GETアクセス時の処理
    if request.method != "POST":
        # フォームの処理
        groupsform = GroupSelectForm(request.user)
        friendsform = FriendsForm(friends=friends, vals=[])  # request.user,
        sel_group = "-"

    # 共通処理
    createform = CreateGroupForm()
    params = {
        "login_user": request.user,
        "groups_form": groupsform,
        "friends_form": friendsform,
        "create_form": createform,
        "group": sel_group,
    }
    return render(request, "sns/groups.html", params)


# Friendの追加処理
@login_required(login_url="/admin/login")
def add(request):
    # 追加するUserを取得
    add_name = request.GET.get("name")
    add_user = User.objects.filter(username=add_name).first()
    # Userが本人だった場合の対処
    if add_user == request.user:
        messages.info(request, "自分自身をFriendに追加することはできません。")
        return redirect(to="index")
    # publicの取得
    (public_user, public_group) = get_public()
    # add_userのFriend数を調べる
    frd_num = Friend.objects.filter(owner=request.user).filter(user=add_user).count()
    # ゼロより大きければ既に登録済み
    if frd_num > 0:
        messages.info(request, add_user + "は既に追加されています。")
        return redirect(to="index")

    # ここからFriendの登録処理
    frd = Friend()
    frd.owner = request.user
    frd.user = add_user
    frd.group = public_group
    frd.save()
    # メッセージを設定
    messages.success(
        request, add_user + "を追加しました！ groupページに移動して、追加したFriendをメンバーに設定してください。"
    )
    return redirect(to="index")


# グループの作成処理
@login_required(login_url="/admin/login/")
def create_group(request):
    # Groupを作り、Userとtitleを設定して保存する
    gp = Group()
    gp.owner = request.user
    gp.title = request.user.username + "の" + request.POST.get("group_name")
    gp.save()
    messages.info(request, "新しいグループを作成しました。")
    return redirect(to="groups")


# メッセージのポスト処理
login_required(login_url="/admin/login/")


def post(request):
    # POST送信の処理
    if request.method == "POST":
        # 送信内容を取得
        gr_name = request.POST.get("groups")
        content = request.POST.get("content")
        # Groupの取得
        group = Group.objects.filter(owner=request.user).filter(title=gr_name)
        if group is None:
            (pub_user, group) = get_public()
        # Messageを作成して保存
        msg = Message()
        msg.owner = request.user
        msg.group = group
        msg.content = content
        msg.save()
        # メッセージを設定
        messages.success(request, "新しいメッセージを投稿しました！")
        return redirect(to="index")

    # GETアクセス時の処理
    if request.method != "POST":
        form = PostForm(request.user)

    # 共通処理
    params = {
        "login_user": request.user,
        "form": form,
    }
    return render(request, "sns/post.html", params)


# 投稿をシェアする
@login_required(login_url="/admin/login/")
def share(request, share_id):
    # シェアするMessageを取得
    share = Message.objects.get(id=share_id)
    print(share)
    # POST送信時の処理
    if request.method == "POST":
        # 送信内容の取得
        gr_name = request.POST.get("groups")
        content = request.POST.get("content")
        # Groupの取得
        group = Group.objects.filter(owner=request.user).filter(title=gr_name).first()
        if group is None:
            (pub_user, group) = get_public()
        # メッセージを作成し、設定をして保存
        msg = Message()
        msg.owner = request.user
        msg.group = group
        msg.content = content
        msg.share_id = share_id
        msg.save()
        share_msg = msg.get_share()
        share_msg.share_count += 1
        share_msg.save()
        # メッセージを設定
        messages.success(request, "メッセージをシェアしました！")
        return redirect(to="index")

    # 共通処理
    form = PostForm(request.user)
    params = {
        "login_user": request.user,
        "form": form,
        "share": share,
    }
    return render(request, "sns/share.html", params)


# goodボタンの処理
@login_required(login_url="/admin/login")
def good(request, good_id):
    # goodするMessageを取得
    good_msg = Message.objects.get(id=good_id)
    # 自分がメッセージにGoodした数を調べる
    is_good = Good.objects.filter(owner=request.user).filter(messages=good_msg).count()
    # ゼロより大きければ既にgood済み
    if is_good > 0:
        messages.success(request, "既にメッセージにはGoodしています。")
        return redirect(to="index")

    # Messageのgood_countを１増やす
    good_msg.good_count += 1
    good_msg.save()
    # Goodを作成し、設定して保存
    good = Good()
    good.owner = request.user
    good.message = good_msg
    good.save()
    # メッセージを設定
    messages.success(request, "メッセージにGoodしました！")
    return redirect(to="index")

    return None


# これ以降は普通の関数===============================================

# 指定されたグループ及び検索文字によるMessageの取得
def get_your_group_message(user, glist, page):
    page_num = 10  # 1ページあたりの表示数
    # publicなUserとGroupを取得する
    (public_user, public_group) = get_public()
    # チェックされたGroupの取得
    groups = Group.objects.filter(Q(owner=user) | Q(owner=public_user)).filter(
        title__in=glist
    )
    # Groupに含まれるFriendの取得
    me_friends = Friend.objects.filter(group__in=groups)
    # FriendのUserをリストにまとめる
    me_users = []
    for f in me_friends:
        me_users.append(f.user)
    # UserリストのUserが作ったGroupの取得
    his_groups = Group.objects.filter(owner__in=me_users)
    his_friends = Friend.objects.filter(user=user).filter(group__in=his_groups)
    me_groups = []
    for hf in his_friends:
        me_groups.append(hf.group)
    # groupがchecked_groupsか、me_groupsに含まれるMessageの取得
    messages = Message.objects.filter(Q(group__in=groups) | Q(group__in=me_groups))
    # ページネーションで指定ページを取得
    page_item = Paginator(messages, page_num)
    return page_item.get_page(page)


# publicなUserとGroupを取得する
def get_public():
    public_user = User.objects.filter(username="public").first()
    public_group = Group.objects.filter(owner=public_user).first()
    return public_user, public_group
