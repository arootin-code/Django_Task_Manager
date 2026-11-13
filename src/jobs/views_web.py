from django.shortcuts import render


def login_page(request):
    return render(request, "jobs/login.html")


def register_page(request):
    return render(request, "jobs/register.html")


def task_list_page(request):
    return render(request, "jobs/task_list.html")


def task_form_page(request):
    return render(request, "jobs/task_form.html")