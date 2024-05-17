from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from gameplay.models import GamePlayer, GameRoom

from account.services import generate_user_token


class TestAccount(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("testuser")
        self.token, _ = generate_user_token(self.user)

    def start_game(self, player1, player2, player1_score=0, player2_score=0):
        game = GameRoom.objects.create()
        async_to_sync(game.add_player)(player1)
        async_to_sync(game.add_player)(player2)
        game.is_started = True
        player = GamePlayer.objects.filter(game_room=game).first()
        player.score = player1_score
        player.save()
        player = GamePlayer.objects.filter(game_room=game).last()
        player.score = player2_score
        player.save()
        game.save()
        return game

    def test_player_history(self):
        url = reverse("history_list")
        opponent = User.objects.create_user("opponent")
        game = self.start_game(self.user, opponent, 5, 2)
        async_to_sync(game.victory)(game.get_player_by_num(1).session_id)
        self.assertTrue(game.is_winner(self.user))

        expected = [
            {
                "player1Name": self.user.username,
                "player1Avatar": "/uploads/avatars/42_Logo.png",
                "player2Name": opponent.username,
                "player2Avatar": "/uploads/avatars/42_Logo.png",
                "isFinished": True,
                "score": "5 - 2",
                "isWinner": True,
                "date": game.created_date.isoformat(),
            }
        ]
        response = self.client.get(url)
        self.assertEqual(response.status_code, 401)

        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200)
        self.assertCountEqual(response.json()["data"], expected)

        game = self.start_game(self.user, opponent, 3, 5)
        async_to_sync(game.victory)(game.get_player_by_num(2).session_id)
        self.assertTrue(game.is_winner(opponent))
        result = {
            "player1Name": self.user.username,
            "player1Avatar": "/uploads/avatars/42_Logo.png",
            "player2Name": opponent.username,
            "player2Avatar": "/uploads/avatars/42_Logo.png",
            "isFinished": True,
            "score": "3 - 5",
            "isWinner": False,
            "date": game.created_date.isoformat(),
        }
        expected.insert(0, result)

        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 2)
        self.assertCountEqual(response.json()["data"], expected)

        game = self.start_game(self.user, opponent, 1, 1)
        result = {
            "player1Name": self.user.username,
            "player1Avatar": "/uploads/avatars/42_Logo.png",
            "player2Name": opponent.username,
            "player2Avatar": "/uploads/avatars/42_Logo.png",
            "isFinished": False,
            "score": "1 - 1",
            "isWinner": False,
            "date": game.created_date.isoformat(),
        }
        expected.insert(0, result)

        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["data"]), 3)
        self.assertCountEqual(response.json()["data"], expected)

        game = GameRoom.objects.create()
        async_to_sync(game.add_player)(self.user)
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {self.token}")
        self.assertEqual(len(response.json()["data"]), 3)
