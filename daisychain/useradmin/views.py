from django.shortcuts import render
from django.core.exceptions import PermissionDenied
from django.views.generic import View
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin


class UserTableView(LoginRequiredMixin, View):

    def get(self, request):
        if request.user.is_staff or request.user.is_superuser:
            template_data = {"users": User.objects.all().values()}
            return render(request, 'useradmin/usertable.html', template_data)
        else:
            raise PermissionDenied()
