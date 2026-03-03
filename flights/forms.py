from django import forms


class FlightSearchForm(forms.Form):
    inbound = forms.CharField(
        max_length=3,
        initial="ARN",
        label="From Airport Code",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., ARN"}),
    )
    outbound = forms.CharField(
        max_length=3,
        initial="BRU",
        label="To Airport Code",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., BRU"}),
    )
    duration_min = forms.IntegerField(
        initial=3,
        min_value=1,
        label="Minimum Duration (days)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    duration_max = forms.IntegerField(
        initial=10,
        min_value=1,
        label="Maximum Duration (days)",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    start_month = forms.CharField(
        max_length=6,
        required=False,
        label="Start Month (YYYYMM)",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "e.g., 202603"}),
    )
    num_months = forms.IntegerField(
        initial=3,
        min_value=1,
        max_value=12,
        label="Number of Months to Scan",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    top = forms.IntegerField(
        initial=10,
        min_value=1,
        label="Number of Results",
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    only_weekends = forms.BooleanField(
        required=False,
        initial=False,
        label="Only Weekend Trips (Fri-Mon)",
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )
    promo_code = forms.CharField(
        max_length=50,
        required=False,
        label="Promotional Code",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Enter promo code (optional)"}
        ),
    )
