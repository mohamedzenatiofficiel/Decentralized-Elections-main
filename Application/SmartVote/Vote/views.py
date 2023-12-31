from django.shortcuts import render,redirect
from Connect.models import Citizen
import os
from django.shortcuts import render,redirect
from AdminSpace.models import Candidate,Election
from django.http import JsonResponse,HttpResponse
# To bypass having a CSRF token
from django.views.decorators.csrf import csrf_exempt
# API definition for task
from AdminSpace.serializers import CandidateSerializer,ElectionSerializer
from rest_framework.decorators import api_view
from cryptography.fernet import Fernet
from dotenv import load_dotenv
load_dotenv('.env')
from Connect.models import Citizen
from django.contrib.auth import authenticate, login
import hashlib
import base64


def index(request):
    if request.user.is_authenticated:
        if not(request.user.is_superuser):
            return render(request,'Vote/index.html')
        else:
            return redirect('/adminspace')
    return render(request,'Vote/home.html',context={'status':1})


def viewElectionStatus(request,name,status):
    if request.user.is_authenticated:
        if not(request.user.is_superuser):
            return render(request,'Vote/viewElection.html', context={'name':name,'status':status})
        else:
            return redirect('/adminspace')
    return redirect('/')

def viewElection(request,name):
    if request.user.is_authenticated:
        if not(request.user.is_superuser):
            return render(request,'Vote/viewElection.html', context={'name':name,'status':"None"})
        else:
            return redirect('/adminspace')
    return redirect('/')

def resultElection(request,name):
    if request.user.is_authenticated:
        if not(request.user.is_superuser):
            return render(request,'Vote/result.html', context={'name':name , 'status':"None"})
        else:
            return redirect('/adminspace')
    return redirect('/')

def resultElectionStatus(request,name,status):
    if request.user.is_authenticated:
        if not(request.user.is_superuser):
            return render(request,'Vote/result.html', context={'name':name, 'status':status})
        else:
            return redirect('/adminspace')
    return redirect('/')

def success(request):
    if request.user.is_authenticated:
        if not(request.user.is_superuser):
            return render(request,'Vote/success.html')
        else:
            return redirect('/adminspace')
    return redirect('/')

# Utils

def isCandidateExist(candidate):
    return Candidate.objects.filter(CandidateName=candidate).exists()

def isElectionExist(name,status='None'):
    if status=='None':
        return Election.objects.filter(ElectionName=name).exists()
    else:
        return Election.objects.filter(ElectionName=name,ElectionStatus=status).exists()

def encrypt(message: bytes, key: bytes) -> bytes:
    return Fernet(key).encrypt(message)

def decrypt(token: bytes, key: bytes) -> bytes:
    return Fernet(key).decrypt(token)

def num_to_random_string(num):
    # Convert number to bytes
    num_bytes = str(num).encode('utf-8')

    # Generate hash value
    hash_object = hashlib.sha256(num_bytes)
    hash_bytes = hash_object.digest()

    # Encode hash value as base64 string
    random_string = base64.b64encode(hash_bytes).decode('utf-8')

    return random_string


#Api
@api_view(['POST'])
def addCandidate(request):
    if(request.method == 'POST'):
        serializer = CandidateSerializer(data=request.data)
        if not(isCandidateExist(request.data['CandidateName'])):
            if(serializer.is_valid()):
                # if okay, save it on the database
                serializer.save()
                # provide a Json Response with the data that was saved
                return JsonResponse(serializer.data, status=201)
        else:
            return JsonResponse({'message':'Ce candidat existe déjà'}, status=400)

        return JsonResponse(serializer.errors, status=400)


def getCandidate(request, pk):
    if(request.method == 'GET'):
        try:
            candidate = Candidate.objects.get(pk=pk)
        except Candidate.DoesNotExist:
            return JsonResponse({'message':"Ce candidat n'existe pas"}, status=400)
        # serialize the tasks
        serializer = CandidateSerializer(candidate, many=False)
        # return the serialized tasks
        return JsonResponse(serializer.data, safe=False)

@csrf_exempt
def getCandidates(request):
    '''
    List all candidates snippets
    '''
    if(request.method == 'GET'):
        # get all the tasks
        candidate = Candidate.objects.all().order_by('CandidateName')
        # serialize the task data
        serializer = CandidateSerializer(candidate, many=True)
        # return a Json response
        return JsonResponse(serializer.data,safe=False)
    else:
        return HttpResponse(status=400)


def getElectionStatus(request,name,status='None'):
    '''
    List all candidates snippets
    '''
    if(request.method == 'GET'):
        # get all the tasks
        try:
            election = Election.objects.filter(ElectionName=name,ElectionStatus=status)
        except Election.DoesNotExist:
            return JsonResponse({'message':"Ce candidat n'existe pas"}, status=400)
        # serialize the task data
        serializer = ElectionSerializer(election, many=True)
        # return a Json response
        return JsonResponse(serializer.data,safe=False)

def getElection(request,name):
    '''
    List all candidates snippets
    '''
    if(request.method == 'GET'):
        try:
            # get all the tasks
            election = Election.objects.filter(ElectionName=name)
            # serialize the task data
            serializer = ElectionSerializer(election, many=True)
            # return a Json response
            return JsonResponse(serializer.data,safe=False)
        except Election.DoesNotExist:
            return JsonResponse({'message':"Ce candidat n'existe pas"}, status=400)

def getElections(request):
    '''
    List all candidates snippets
    '''
    if(request.method == 'GET'):
        # get all the tasks
        election = Election.objects.filter(ElectionBlind=False).order_by('ElectionName')
        # serialize the task data
        serializer = ElectionSerializer(election, many=True)
        # return a Json response
        return JsonResponse(serializer.data,safe=False)

@api_view(['DELETE'])
def delCandidate(request, pk):
    '''
    Delete a candidate
    '''
    if(request.method == 'DELETE'):
        # get the task with the id
        try:
            candidate = Candidate.objects.get(CandidateName=pk)
        except Candidate.DoesNotExist:
            return HttpResponse({'message':"Ce candidat n'existe pas"},status=400)

        # check if is in an election
        for election in Election.objects.all().values_list('ElectionCandidates',flat=True):
            if pk in election:
                return JsonResponse({"message":"Candidate is in an election, delete election before deleting the candidate"},status=400)

        # delete files
        try:
            if(candidate.CandidateImage):
                os.remove(candidate.CandidateImage.path)
        except:
            pass
        try:
            if(candidate.CandidateProgram):
                os.remove(candidate.CandidateProgram.path)
        except:
            pass
        # delete candidate
        candidate.delete()
        # return a Json response
        return JsonResponse({'message':'Candidate deleted successfully'}, status=204)
    else:
        return HttpResponse(status=400)

@api_view(['PUT'])
def updateCandidate(request, pk):
    '''
    Update a candidate
    '''
    if(request.method == 'PUT'):
        # get the task with the id
        try:
            candidate = Candidate.objects.get(CandidateName=pk)
        except Candidate.DoesNotExist:
            return JsonResponse({'message':"Ce candidat n'existe pas"},status=400)
        
        for election in Election.objects.all().values_list('ElectionCandidates',flat=True):
            if pk in election:
                return JsonResponse({"message":"Candidate is in an election, delete election before update the candidate"},status=400)

        serializer = CandidateSerializer(candidate,data=request.data)
            
        # check if the data is valid
        if(serializer.is_valid()):
            try:
                print("request.data['CandidateImage'] : ")
                print(request.data['CandidateImage'])
            except:
                pass
            try:
                print("candidate.CandidateImage : ")
                print(candidate.CandidateImage)
            except:
                pass

            try :
                if request.data['CandidateImage']:
                    if(candidate.CandidateImage != request.data['CandidateImage']):
                        try:
                            os.remove(candidate.CandidateImage.path)
                        except:
                            pass
                else:
                    try:
                        os.remove(candidate.CandidateImage.path)
                    except:
                        pass
            except:
                pass

            try :
                if request.data['CandidateProgram']:
                    if(candidate.CandidateProgram != request.data['CandidateProgram']):
                        try:
                            os.remove(candidate.CandidateProgram.path)
                        except:
                            pass
                else:
                    try:
                        os.remove(candidate.CandidateProgram.path)
                    except:
                        pass
            except:
                pass

            serializer.save()

            if(serializer.data["CandidateName"] != pk):
                print("name changed")
                try:
                    candidate = Candidate.objects.get(CandidateName=pk)
                    candidate.delete()
                except Candidate.DoesNotExist:
                    return HttpResponse({'message':"Ce candidat n'existe pas"},status=400)

            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
    
@api_view(['POST'])
def addElection(request):
    if(request.method == 'POST'):
        request.data._mutable=True
        request.data['ElectionApiKey']= encrypt(request.data['ElectionApiKey'].encode(), os.environ.get("DECRYPT_KEY").encode())
        serializer = ElectionSerializer(data=request.data)
        if not(isElectionExist(request.data['ElectionName'],request.data['ElectionStatus'])):
            if(serializer.is_valid()):
                # if okay, save it on the database
                serializer.save()
                # provide a Json Response with the data that was saved
                return JsonResponse(serializer.data, status=201)
            else:
                 return JsonResponse(serializer.errors, status=400)
        else:
            return JsonResponse({'message':'Cette élection existe déjà'}, status=400)
       
@api_view(['DELETE'])
def delElectionStatus(request, pk, status='None'):
    '''
    Delete a election
    '''
    if(request.method == 'DELETE'):
        # get the task with the id
        try:
            election = Election.objects.get(ElectionName=pk,ElectionStatus=status)
        except Election.DoesNotExist:
            return JsonResponse({'message':"Cette élection n'existe pas"},status=400)

        # delete election
        election.delete()
        # return a Json response
        return JsonResponse({'message':'Election deleted successfully'}, status=204)
    else:
        return HttpResponse(status=400)

@api_view(['DELETE'])
def delElection(request, pk):
    '''
    Delete a election
    '''
    if(request.method == 'DELETE'):
        # get the task with the id
        try:
            election = Election.objects.get(ElectionName=pk,ElectionStatus="")
        except Election.DoesNotExist:
            return JsonResponse({'message':"Cette élection n'existe pas"},status=400)

        # delete election
        election.delete()
        # return a Json response
        return JsonResponse({'message':'Election deleted successfully'}, status=204)
    else:
        return HttpResponse(status=400)

@api_view(['PUT'])
def updateElection(request, pk):
    '''
    Update a election
    '''
    if(request.method == 'PUT'):
        # get the task with the id
        try:
            election = Election.objects.get(ElectionName=pk)
        except Election.DoesNotExist:
            return JsonResponse({'message':"Cette élection n'existe pas"},status=400)
        
        serializer = ElectionSerializer(election,data=request.data)
            
        # check if the data is valid
        if(serializer.is_valid()):
            serializer.save()
            if(serializer.data["ElectionName"] != pk):
                print("name changed")
                try:
                    election = Election.objects.get(ElectionName=pk)
                    election.delete()
                except Election.DoesNotExist:
                    return HttpResponse({'message':"Cette élection n'existe pas"},status=400)

            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

@api_view(['PUT'])
def updateElectionStatus(request, pk, status='None'):
    '''
    Update a election
    '''
    if(request.method == 'PUT'):
        # get the task with the id
        try:
            election = Election.objects.get(ElectionName=pk,ElectionStatus=status)
        except Election.DoesNotExist:
            return JsonResponse({'message':"Cette élection n'existe pas"},status=400)
        
        serializer = ElectionSerializer(election,data=request.data)
            
        # check if the data is valid
        if(serializer.is_valid()):
            serializer.save()
            if(serializer.data["ElectionName"] != pk):
                print("name changed")
                try:
                    election = Election.objects.get(ElectionName=pk)
                    election.delete()
                except Election.DoesNotExist:
                    return HttpResponse({'message':"Cette élection n'existe pas"},status=400)

            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

@api_view(['GET'])
def isElectionExistStatusAPI(request, name, status):
    '''
    Check if an election exist
    '''
    if(request.method == 'GET'):
        # get the task with the id
        try:
            election = Election.objects.get(ElectionName=name,ElectionStatus=status)
        except Election.DoesNotExist:
            return JsonResponse({'message':"Cette élection n'existe pas"},status=201)
        return JsonResponse({'message':'Cette élection existe déjà'}, status=201)

@api_view(['GET'])
def isElectionExistAPI(request, name):
    '''
    Check if an election exist
    '''
    if(request.method == 'GET'):
        # get the task with the id
        try:
            election = Election.objects.get(ElectionName=name,ElectionStatus="")
        except Election.DoesNotExist:
            return JsonResponse({'message':"Cette élection n'existe pas"},status=201)
        return JsonResponse({'message':'Cette élection existe déjà'}, status=201)

@api_view(['GET'])
def getIdEncrypted(request, pk):
    try:
        return JsonResponse({'id_encrypted':num_to_random_string(pk)}, status=201)
    except KeyError:
        return JsonResponse({'message':"Identifiant introuvable"},status=400)

@api_view(['GET'])
def getAPIKeyDecrypted(request, apikey):
    try:
        return JsonResponse({'ElectionApiKey':decrypt(apikey, os.environ.get("DECRYPT_KEY").encode()).decode()}, status=201)
    except Election.DoesNotExist:
        return JsonResponse({'message':"Cette élection n'existe pas"},status=400)
    