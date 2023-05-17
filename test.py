import pytest
from forms import RegistrationForm, LoginForm, TimeOffRequestForm, BlacklistClientForm, EditBlacklistedClientForm, CreatePostForm, CommentForm, FeatureSuggestionForm


def test_registration_form():
    form = RegistrationForm(
        username="test",
        password="password",
        email="test@gmail.com",
        first_name="First",
        last_name="Last"
    )
    assert form.validate() == True


def test_login_form():
    form = LoginForm(username="test", password="password")
    assert form.validate() == True


def test_time_off_request_form():
    form = TimeOffRequestForm(
        shift_coverage_date="2023-05-30",
        covering_user=1,
        reason='vacation',
        shift_time="09:00 - 17:00",
        request_acknowledged=True
    )
    assert form.validate() == True


def test_blacklist_client_form():
    form = BlacklistClientForm(
        client_name="Client Name",
        reason="Reason for blacklisting",
        blacklisting_person="Employee Name"
    )
    assert form.validate() == True


def test_edit_blacklisted_client_form():
    form = EditBlacklistedClientForm(
        client_name="Client Name",
        reason="Reason for blacklisting",
        blacklisting_person="Employee Name"
    )
    assert form.validate() == True


def test_create_post_form():
    form = CreatePostForm(content="This is a new post")
    assert form.validate() == True


def test_comment_form():
    form = CommentForm(content="This is a comment")
    assert form.validate() == True


def test_feature_suggestion_form():
    form = FeatureSuggestionForm(suggestion="This is a feature suggestion")
    assert form.validate() == True
