import json
import random
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .models import GameRoom
from asgiref.sync import sync_to_async

class GameConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_code = self.scope['url_route']['kwargs']['room_code']
        self.room_group_name = f'game_{self.room_code}'
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()
        await self.broadcast_status()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
        await self.broadcast_status()

    async def broadcast_status(self):
        # গ্রুপে কতজন কানেক্টেড আছে তা চেক করা
        count = len(self.channel_layer.groups.get(self.room_group_name, {}))
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'status_update',
                'player_count': count
            }
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        action = data.get('action')
        mode = data.get('mode', 'double') 
        
        room = await sync_to_async(GameRoom.objects.get)(room_code=self.room_code)

        if action == 'reset':
            await self.reset_room(room)
            
            # ডাটাবেজ থেকে লেটেস্ট স্টেট আবার টেনে আনা
            room = await sync_to_async(GameRoom.objects.get)(room_code=self.room_code)
            
            # ১. প্রথমে সবাইকে খালি বোর্ড ব্রডকাস্ট করুন
            await self.broadcast_game_state(room)

            # ২. যদি Single Player হয় এবং CPU-এর টার্ন হয়, তবে CPU চাল দিবে
            human_player = data.get('player', 'X')
            ai_player = 'O' if human_player == 'X' else 'X'
            
            if mode == 'single' and room.turn == ai_player:
                await asyncio.sleep(0.8) # রিসেট হওয়ার পর একটু পজ
                await self.ai_move(room, human_player)
                # ai_move এর ভেতরেই ডাটাবেজ সেভ এবং ফাইনাল ব্রডকাস্ট হবে
        
        else:
            index = data.get('index')
            player = data.get('player')

            # চাল দেওয়ার ভ্যালিডেশন
            if index is not None and not room.is_over and room.board[index] is None and room.turn == player:
                await self.make_move(room, index, player)
                
                # চাল দেওয়ার পর যদি Single Player হয় এবং গেম শেষ না হয়
                if mode == 'single' and not room.is_over:
                    await asyncio.sleep(0.5)
                    await self.ai_move(room, player)

        # সবশেষে বর্তমান অবস্থা ব্রডকাস্ট
        await self.broadcast_game_state(room)

    async def make_move(self, room, index, player):
        history = list(room.x_history) if player == 'X' else list(room.o_history)
        
        # ৩টির বেশি হলে প্রথমটি রিমুভ
        if len(history) >= 3:
            oldest = history.pop(0)
            room.board[oldest] = None
        
        room.board[index] = player
        history.append(index)
        
        if player == 'X': room.x_history = history
        else: room.o_history = history

        room.turn = 'O' if player == 'X' else 'X'
        self.check_winner(room)
        await sync_to_async(room.save)()

    async def ai_move(self, room, human_player):
        ai_player = 'O' if human_player == 'X' else 'X'
        empty_indices = [i for i, val in enumerate(room.board) if val is None]
        
        if empty_indices and not room.is_over:
            ai_choice = random.choice(empty_indices)
            await self.make_move(room, ai_choice, ai_player)

    def check_winner(self, room):
        win_lines = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a, b, c in win_lines:
            if room.board[a] == room.board[b] == room.board[c] and room.board[a] is not None:
                room.winner = room.board[a]
                room.winning_line = f"line-{a}-{b}-{c}"
                room.is_over = True
                room.next_starter = room.winner # উইনার পরের ম্যাচে প্রথম চাল দিবে
                return

    async def reset_room(self, room):
        room.board = [None] * 9
        room.x_history, room.o_history = [], []
        room.turn = room.next_starter 
        room.winner = None
        room.winning_line = None
        room.is_over = False
        await sync_to_async(room.save)()

    async def broadcast_game_state(self, room):
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'game_message',
                'board': room.board,
                'turn': room.turn,
                'winner': room.winner,
                'winning_line': room.winning_line
            }
        )

    async def game_message(self, event):
        await self.send(text_data=json.dumps(event))

    async def status_update(self, event):
        await self.send(text_data=json.dumps(event))