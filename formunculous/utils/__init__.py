from formunculous.forms import *

from django.forms.formsets import formset_factory
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

# This takes a form and builds a formunculous datastructure for
# rendering the form into a template
def build_template_structure(form, ad, reviewer_only=False):

    # create structure for the template that looks like
    # form-> (group, pre-text, post-text, required)
    inc = {}
    fields = []
    for field in ad.fielddefinition_set.filter(reviewer_only=reviewer_only):
        field_dict = {'group': field.group, 
                      'pre_text': mark_safe(field.pre_text), 
                      'post_text': mark_safe(field.post_text),
                      'field': form.__getitem__(field.slug),
                      'required': field.require}
        fields.append(field_dict)
        inc[field.slug] = True

    # Got all the DB fields in the form, now run through any extras that
    # may have shown up.
    if not reviewer_only or fields!=[]:
        for field in form.fields:
            if not inc.has_key(field):
                field_dict = {'group': False, 'pre_text': None, 'post_text': None,
                              'field': form.__getitem__(field), 
                              'required': form.__getitem__(field).field.required,}
                # Append one down to avoid first and last loop counters
                fields.insert(1,field_dict)
    return fields

def get_formsets(ad, request, user):

    formsets = []
    sub_apps = ad.applicationdefinition_set.all()
    for sub_app in sub_apps:
        sub_ad = sub_app.subapplicationdefinition_set.get()
        SubAppFormset = formset_factory(ApplicationForm,
                                        formset=FormunculousBaseFormSet,
                                        extra=sub_ad.extras,
                                        max_num = sub_ad.max_entries)
        formset = SubAppFormset(data=request.POST, 
                                files=request.FILES, 
                                app_def=sub_app, user=user, 
                                minimum = sub_ad.min_entries,
                                prefix=sub_app.slug)
        formsets.append(formset)
    return formsets

def validate_formsets(formsets):
    valid = True
    if not formsets:
        return True

    for formset in formsets:
        for subform in formset.forms:
            if subform.changed_data:
                if not subform.is_valid():
                    valid = False    
    return valid


def fully_validate_formsets(formsets):
    valid = True
    if not formsets:
        return valid
    for formset in formsets:
        min_count = formset.minimum
        form_count = 0
        for subform in formset.forms:
            if not subform.is_valid():
                valid = False
            if subform.app or subform.changed_data:
                if not subform.check_required():
                    valid = False
                form_count += 1
        if form_count < min_count and min_count != 0:
            formset._non_form_errors = ErrorList([_("This group requires %s or \
                                                  more entries" % min_count),])
            valid = False

    return valid

def save_formsets(formsets, parent_app, user):
    for formset in formsets:
        for subform in formset.forms:
            if subform.changed_data:
                if not subform.app:
                    subform.app = Application(
                        parent=parent_app,
                        user = user,
                        app_definition = formset.app_def)
                subform.save()
    
def get_sub_app_fields(parent_app):

    parent_ad = parent_app.app_definition
    sub_ads = parent_ad.applicationdefinition_set.all()

    if not sub_ads:
        return None

    sub_ad_coll = []
    for sub_ad in sub_ads:
        sub_apps = parent_app.application_set.filter(app_definition = sub_ad)
        sub_apps_coll = []
        for sub_app in sub_apps:
            sub_apps_coll.append({ 'fields': sub_app.get_field_values(),})

        sub_ad_coll.append( { 'sub_ad': sub_ad, 'sub_apps': sub_apps_coll } )

    return sub_ad_coll
