from django import forms

class StartForm(forms.Form):
    api_token = forms.CharField(
        label="Canvas API Token",
        widget=forms.PasswordInput(attrs={"autocomplete": "off"}, render_value=True),
        required=True
    )
    course_ids_raw = forms.CharField(
        label="Course IDs",
        help_text="Comma-separated Canvas course IDs",
        required=True
    )
    canvas_api_url = forms.CharField(
        label="Canvas API URL",
        help_text="Enter the Canvas API URL for your institution. e.g. https://ivylearn.ivytech.edu/api/v1",
        required=True
    )
    start_date = forms.CharField( widget=forms.TextInput(attrs={'id': 'start_date'}))
    end_date = forms.CharField( widget=forms.TextInput(attrs={'id': 'end_date'}))


class ConfirmCoursesForm(forms.Form):
    courses = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label="Select courses to include"
    )

    def __init__(self, *args, **kwargs):
        course_choices = kwargs.pop("course_choices", [])
        super().__init__(*args, **kwargs)
        self.fields["courses"].choices = course_choices

class MessageTemplateForm(forms.Form):
    template_congrats = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'template_congrats'})
    )
    template_encourage = forms.CharField(
        widget=forms.HiddenInput(attrs={'id': 'template_encourage'})
    )
