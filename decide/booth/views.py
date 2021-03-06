import json, requests
from django.views.generic import TemplateView
from django.conf import settings
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.status import (HTTP_200_OK, HTTP_404_NOT_FOUND)
from django.shortcuts import render, redirect
from django.contrib.auth import logout as do_logout
from django.contrib.auth import login as do_login
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from authentication.models import Perfil
from base import mods
from booth.form import registerForm, profileForm
from django.contrib import auth
from census.models import Census
from voting.models import Voting
from booth.models import profile
from store.models import Vote
from django.shortcuts import render, redirect
from Crypto.Random import random
from rest_framework.authtoken.models import Token
from django.utils import timezone


def booth(request, **kwargs):
    if request.method == 'GET':
        try:
            voting_id = kwargs.get('voting_id')
            if voting_checks(voting_id):
                voting = Voting.objects.get(pk=voting_id)
                candidatures = voting.candidatures.all()

                list_candidatures = []

                for candidature in candidatures:
                    res = {
                        'presidentes': candidature.candidates.filter(type='PRESIDENCIA'),
                        'candidatos': candidature.candidates.filter(type='CANDIDATO'),
                        'candidatura': candidature.name

                    }
                    list_candidatures.append(res)
                return render(request, 'booth/booth.html', {'list': list_candidatures, 'voting': voting})
            else:
                raise Http404
        except:
            raise Http404
    if request.method == 'POST':
        try:
            voting_id = kwargs.get('voting_id')
            if voting_checks(voting_id):
                voting = Voting.objects.get(pk=voting_id)
                # Presidente is required
                pres = str(request.POST['presidente'])
                cand = request.POST.getlist('candidatos')
                # Get new option. Format: <id_presidente>000<id_candidato1>000<id_candidato2000>
                option = get_option(pres, cand)
                user_id = request.user.id
                token = str(Token.objects.get(user=request.user))

                bigpk = {
                    'p': str(voting.pub_key.p),
                    'g': str(voting.pub_key.g),
                    'y': str(voting.pub_key.y),
                }

                vote = encrypt(bigpk, option)

                send_data(request, user_id, token, voting_id, vote)

                return render(request, 'booth/success.html', {'user': request.user})
            else:
                raise Http404
        except:
            raise Http404


def send_data(request, user, token, voting, vote):
    data = json.dumps({
        'voter': user,
        'token': token,
        'voting': voting,
        'vote': {'a': str(vote[0]), 'b': str(vote[1])}
    })

    headers = {
        'Content-type': 'application/json',
        'Authorization': 'Token ' + token
    }

    r = requests.post(url='http://' + request.META['HTTP_HOST'] + '/gateway/store/', data=data, headers=headers)
    return r


def encrypt(pk, M):
    k = random.StrongRandom().randint(1, int(pk["p"]) - 1)
    a = pow(int(pk["g"]), k, int(pk["p"]))
    b = (pow(int(pk["y"]), k, int(pk["p"])) * M) % int(pk["p"])
    return a, b


def votinglist(request):
    user_id = request.user.id

    if user_id is not None:
        census = Census.objects.filter(voter_id=user_id)
        res = []

        for c in census:
            voting_id = c.voting_id
            # Only for list view
            try:
                if voting_id is not None and voting_checks(voting_id):
                    voting = Voting.objects.get(pk=voting_id)
                    res.append(voting)
            except Voting.DoesNotExist:
                pass

        return render(request, 'booth/votinglist.html', {'res': res})
    else:
        # If user is not log in, redirect to log in page.
        return PageView.login(request)


class PageView(TemplateView):

    def register(request):
        if request.user.is_authenticated:
            return redirect('/')

        errors = []
        form = None
        if request.method == "POST":
            form = registerForm(request.POST)
            if not form.is_valid():
                errors.append(-1)
            else:
                if request.POST.get('first_name') == "":
                    errors.append(0)
                if request.POST.get('last_name') == "":
                    errors.append(1)
                if request.POST.get('password') != request.POST.get('confirm_password'):
                    errors.append(2)
                if request.POST.get('email') == "":
                    errors.append(3)
                if not request.POST.get('edad').isdigit():
                    errors.append(4)

                if len(errors) == 0:
                    # Si el usuario se crea correctamente
                    user = form.save()
                    user.set_password(form.cleaned_data['password'])
                    user.save()
                    profile.objects.create(user=user, edad=request.POST.get('edad'),
                                           provincia=request.POST.get('provincia'),
                                           municipio=request.POST.get('municipio'),
                                           sexo=request.POST.get('sexo')).save()
                    Perfil.objects.create(user=user, sexo=request.POST.get('sexo'),
                                          edad=request.POST.get('edad'),
                                          municipio=request.POST.get('municipio'),
                                          ).save()

                    return redirect('/login')

        return render(request, "booth/register.html", {'form': form, 'errors': errors, 'lenErrors': len(errors)})

    def login(request):
        if request.user.is_authenticated:
            return redirect('/')

        errors = 0
        if request.method == "POST":
            # Recuperamos las credenciales validadas
            username = request.POST.get('username')
            password = request.POST.get('password')

            # Verificamos las credenciales del usuario
            user = authenticate(request, username=username, password=password)
            # Si existe un usuario con ese nombre y contraseña
            if user is not None:
                do_login(request, user)
                return redirect('/')
            else:
                errors = 1

        return render(request, "booth/login.html", {'errors': errors})

    def logout(request):
        do_logout(request)
        return redirect('/')

    def index(request):
        return render(request, 'booth/index.html')

    def profile(request):
        user = request.user
        first_name = request.user.first_name
        last_name = request.user.last_name
        email = request.user.email
        if profile.objects.filter(user=user).exists():
            provincia = profile.objects.get(user=user).provincia
            edad = profile.objects.get(user=user).edad
            municipio = profile.objects.get(user=user).municipio
            sexo = profile.objects.get(user=user).sexo
        else:
            provincia = ''
            edad = ''
            municipio = ''
            sexo = ''

        errors = []
        form = None
        if request.method == "POST":
            form = profileForm(request.POST)
            if not form.is_valid():
                errors.append(-1)
            else:
                profilee = profile.objects.filter(user=user)
                perfil = Perfil.objects.filter(user=user)
                if request.POST.get('first_name') == "":
                    errors.append(0)
                if request.POST.get('last_name') == "":
                    errors.append(1)
                if request.POST.get('email') == "":
                    errors.append(2)
                if request.POST.get('municipio') == "":
                    errors.append(3)
                if request.POST.get('provincia') == "":
                    errors.append(4)
                if not request.POST.get('edad').isdigit():
                    errors.append(5)

                if len(errors) == 0:
                    user.first_name = request.POST.get('first_name')
                    user.last_name = request.POST.get('last_name')
                    user.email = request.POST.get('email')
                    user.save()

                    first_name = request.POST.get('first_name')
                    last_name = request.POST.get('last_name')
                    email = request.POST.get('email')
                    edad = request.POST.get('edad')
                    municipio = request.POST.get('municipio')
                    sexo = request.POST.get('sexo')
                    provincia = request.POST.get('provincia')

                    if not profilee.exists():
                        profile.objects.create(user=request.user, edad=request.POST.get('edad'),
                                               provincia=request.POST.get('provincia'),
                                               municipio=request.POST.get('municipio'), sexo=request.POST.get('sexo'))
                        Perfil.objects.create(user=request.user, edad=request.POST.get('edad'),
                                              municipio=request.POST.get('municipio'), sexo=request.POST.get('sexo'))
                    else:
                        profilee = profile.objects.get(user=user)
                        profilee.edad = request.POST.get('edad')
                        profilee.provincia = request.POST.get('provincia')
                        profilee.municipio = request.POST.get('municipio')
                        profilee.sexo = request.POST.get('sexo')
                        profilee.save()

                        perfil = Perfil.objects.get(user=user)
                        perfil.edad = request.POST.get('edad')
                        perfil.municipio = request.POST.get('municipio')
                        perfil.sexo = request.POST.get('sexo')
                        perfil.save()

            return render(request, 'booth/profile.html',
                          {'provincia': provincia, 'municipio': municipio, 'edad': edad, 'sexo': sexo, 'is_submit': 1,
                           'form': form, 'first_name': first_name, 'last_name': last_name, 'email': email,
                           'errors': errors, 'lenErrors': len(errors)})

        return render(request, 'booth/profile.html',
                      {'provincia': provincia, 'municipio': municipio, 'edad': edad, 'sexo': sexo, 'is_submit': 0,
                       'form': form, 'first_name': first_name, 'last_name': last_name, 'email': email, 'errors': errors,
                       'lenErrors': len(errors)})


class GetVoting(APIView):
    def post(self, request):
        vid = request.data.get('voting', '')
        try:
            r = mods.get('voting', params={'id': vid})
            for k, v in r[0]['pub_key'].items():
                r[0]['pub_key'][k] = str(v)
            return Response(r[0], status=HTTP_200_OK)
        except:
            return Response({}, status=HTTP_404_NOT_FOUND)


def check_date(date):
    today = timezone.now()
    if date > today:
        # If voting end_date is before today:
        return True
    else:
        return False


def voting_checks(voting_id):
    aux = False
    voting = Voting.objects.get(pk=voting_id)
    # Check dates. Voting must be between stablished dates
    if (voting.end_date is None or check_date(voting.end_date)) and (
            voting.start_date is None or not check_date(voting.start_date)):
        # Check that voter doesn't send other vote to this voting
        try:
            Vote.objects.get(voting_id=voting_id)
        except Vote.DoesNotExist:
            aux = True
    return aux


def get_option(presidente, candidatos):
    option = presidente + '000'
    for candidato in candidatos:
        option = option + candidato + '000'
    return int(option)
