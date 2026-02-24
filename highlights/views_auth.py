from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib import messages


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect("/")
        messages.error(request, "Invalid credentials")

    return render(request, "auth/login.html")


def signup_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        if User.objects.filter(username=username).exists():
            messages.error(request, "User already exists")
        else:
            user = User.objects.create_user(username=username, password=password)
            login(request, user)
            return redirect("/")

    return render(request, "auth/signup.html")


def logout_view(request):
    logout(request)
    return redirect("/")
