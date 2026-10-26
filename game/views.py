import uuid
from django.shortcuts import render, redirect, get_object_or_404
from .models import GameRoom

def index(request):
    """গেমের মেইন মেনু বা হোম পেজ"""
    return render(request, 'index.html')

def tic_tac_toe_online(request, room_code):
    """গেম খেলার মূল লজিক এবং লিঙ্ক হ্যান্ডলিং"""
    room, created = GameRoom.objects.get_or_create(room_code=room_code)
    
    # রুম নতুন হলে বা বোর্ড না থাকলে ইনিশিয়ালাইজ করা
    if created or not room.board:
        room.board = [None] * 9
        room.x_history = []
        room.o_history = []
        room.turn = 'X'
        room.save()

    # URL থেকে p (player) এবং mode প্যারামিটার নেওয়া
    p_param = request.GET.get('p')
    mode = request.GET.get('mode', 'double')

    # বন্ধু যখন সরাসরি লিঙ্কে ঢুকবে (p প্যারামিটার ছাড়া)
    if not p_param:
        # আপনি X হিসেবে আছেন, তাই তাকে O দেওয়া হবে
        player_type = 'O'
    else:
        player_type = p_param.upper()

    return render(request, 'game.html', {
        'room_code': room_code,
        'player_type': player_type,
        'mode': mode,
        'board': room.board,
        'turn': room.turn,
        'winner': room.winner,
        'winning_line': room.winning_line,
    })