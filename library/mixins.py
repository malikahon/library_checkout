from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin that requires the user to be authenticated AND have is_staff=True.

    - Unauthenticated users are redirected to LOGIN_URL (LoginRequiredMixin).
    - Authenticated non-staff users receive a 403 Forbidden (UserPassesTestMixin).
    """

    def test_func(self):
        return self.request.user.is_staff
