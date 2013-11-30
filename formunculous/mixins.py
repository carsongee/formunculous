"""
Useful mixins classes for views
"""

from django.contrib.auth.decorators import permission_required
from django.utils.decorators import method_decorator

class ChangeFormMixin(object):
    @method_decorator(permission_required('formunculous.change_form'))
    def dispatch(self, request, *args, **kwargs):
        return super(ChangeFormMixin, self).dispatch(request, *args, **kwargs)

class AddFormMixin(object):
    @method_decorator(permission_required('formunculous.add_form'))
    def dispatch(self, request, *args, **kwargs):
        return super(AddFormMixin, self).dispatch(request, *args, **kwargs)

class DeleteFormMixin(object):
    @method_decorator(permission_required('formunculous.delete_form'))
    def dispatch(self, request, *args, **kwargs):
        return super(DeleteFormMixin, self).dispatch(request, *args, **kwargs)
