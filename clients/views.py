from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from .forms import ClientForm
from .models import Client


@login_required
def client_list(request):
    query = request.GET.get(
        "q",
        "",
    ).strip()

    clients = Client.objects.filter(
        user=request.user,
    )

    if query:
        clients = clients.filter(
            Q(name__icontains=query)
            | Q(email__icontains=query)
            | Q(company_name__icontains=query)
            | Q(phone__icontains=query)
        )

    return render(
        request,
        "clients/client_list.html",
        {
            "clients": clients,
            "query": query,
        },
    )


@login_required
def client_detail(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
        user=request.user,
    )

    return render(
        request,
        "clients/client_detail.html",
        {
            "client": client,
        },
    )


@login_required
def client_create(request):
    if request.method == "POST":
        form = ClientForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            client = form.save(
                commit=False,
            )

            client.user = request.user
            client.save()

            messages.success(
                request,
                "Client created successfully.",
            )

            return redirect(
                "client_detail",
                pk=client.pk,
            )
    else:
        form = ClientForm(
            user=request.user,
        )

    return render(
        request,
        "clients/client_form.html",
        {
            "form": form,
            "page_title": "Add client",
            "button_text": "Create client",
        },
    )


@login_required
def client_update(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        form = ClientForm(
            request.POST,
            instance=client,
            user=request.user,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                "Client updated successfully.",
            )

            return redirect(
                "client_detail",
                pk=client.pk,
            )
    else:
        form = ClientForm(
            instance=client,
            user=request.user,
        )

    return render(
        request,
        "clients/client_form.html",
        {
            "form": form,
            "client": client,
            "page_title": "Edit client",
            "button_text": "Save changes",
        },
    )


@login_required
def client_delete(request, pk):
    client = get_object_or_404(
        Client,
        pk=pk,
        user=request.user,
    )

    if request.method == "POST":
        client_name = client.name
        client.delete()

        messages.success(
            request,
            f"{client_name} was deleted.",
        )

        return redirect(
            "client_list",
        )

    return render(
        request,
        "clients/client_confirm_delete.html",
        {
            "client": client,
        },
    )