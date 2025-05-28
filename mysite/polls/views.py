from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Question, Choice

# Without using raw SQL queries, we can prevent SQL injection.
# Django's querysets are protected because they are constructed using query parameterization.
# By filtering the questions so that the publish date is less or equal to this moment,
# users can't access data they shouldn't, like unpublished questions.
# This way broken access control is prevented.
# filter() method returns only the rows that match the search,
# also this way Django's ORM protects itself from SQL injection.

# Code with flaws is commented inside the functions. Fixed code is the not commented, actual code.

# SQL Injection is a vulnerability that could occur in all of the functions in this file.
# It is demonstrated only in the following function called "demonstrate_sql_injection".¨
# This function demonstrates how raw SQL queries shoudl not be used in any of this file's functions.

def demonstrate_sql_injection(request):
    user_input = request.GET.get("filter")
    
    if user_input:
        query = f"SELECT * FROM polls_question WHERE {user_input} ORDER BY pub_date DESC LIMIT 5"
    else:
        now = timezone.now().isoformat()
        query = f"SELECT * FROM polls_question WHERE pub_date <= '{now}' ORDER BY pub_date DESC LIMIT 5"

    # pylint: disable=no-member
    results = Question.objects.raw(query)
    return render(request, "polls/vulnerable_page.html", {"latest_question_list": results, "user_input": user_input or ""})

class IndexView(generic.ListView):
    template_name = "polls/index.html"
    context_object_name = "latest_question_list"

    def get_queryset(self):
        """Version with Broken Access Control vulnerability:
        
        return Question.objects.all().order_by("-pub_date")[:5]
        """

        # pylint: disable=no-member
        return Question.objects.filter(pub_date__lte=timezone.now()).order_by("-pub_date")[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = "polls/detail.html"

    def get_queryset(self):
        """Version with Broken Access Control vulnerability:
        
        return Question.objects.all()
        """

        # pylint: disable=no-member
        return Question.objects.filter(pub_date__lte=timezone.now())

class ResultsView(generic.DetailView):
    model = Question
    template_name = "polls/results.html"

    def get_queryset(self):
        """Version with Broken Access Control vulnerability:
        
        return Question.objects.all()
        """

        # pylint: disable=no-member
        return Question.objects.filter(pub_date__lte=timezone.now())

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        # Django's ORM sanitizes the primary key, no unvalidated user input injected to SQL queries
        selected_choice = question.choice_set.get(pk=request.POST["choice"])
    # pylint: disable=no-member
    except (KeyError, Choice.DoesNotExist):
        return render(request, "polls/detail.html", {"question": question,
                                                     "error_message": "You didn't select a choice.",
                                                     }, )
    else:
        selected_choice.votes += 1
        selected_choice.save()

    return HttpResponseRedirect(reverse("polls:results", args=(question.id,)))