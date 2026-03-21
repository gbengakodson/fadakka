from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Coin

# Simple test view
def test_coins(request):
    return JsonResponse({"message": "Test endpoint works!"})

class CoinListView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request):
        coins = Coin.objects.all()
        data = [{"id": c.id, "symbol": c.symbol, "name": c.name} for c in coins]
        return Response(data)

class CoinDetailView(APIView):
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        return Response({"message": f"Coin detail for {pk}"})


from django.shortcuts import render

def test_page(request):
    return render(request, 'test.html')