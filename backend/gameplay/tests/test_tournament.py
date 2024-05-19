from account.services import generate_user_token
from asgiref.sync import async_to_sync
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from gameplay.models import GamePlayer, GameRoom, Tournament, TournamentPlayer


class TestTournament(TestCase):
    def setUp(self):
        self.users = [
            User.objects.create_user("test1"),
            User.objects.create_user("test2"),
            User.objects.create_user("test3"),
            User.objects.create_user("test4"),
        ]
        assert User.objects.count() == 4
        self.tournament = Tournament.objects.create()

    async def add_players(self, count=4):
        async for user in User.objects.all():
            if count == 0:
                return
            count -= 1
            await self.tournament.add_player(user)

    def test_create_tournament(self):
        url = reverse("user_tournament")
        self.assertEqual(Tournament.objects.count(), 1)
        payload = {"game_type": "pong"}

        response = self.client.post(
            url,
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        token, _ = generate_user_token(self.users[0])
        response = self.client.post(
            url,
            payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json().get("success"))
        self.assertEqual(Tournament.objects.count(), 2)
        tournament = Tournament.objects.last()
        self.assertEqual(tournament.players.count(), 1)
        self.assertEqual(async_to_sync(tournament.get_host)(), self.users[0])

    def test_user_tournament(self):
        url = reverse("user_tournament")
        token, _ = generate_user_token(self.users[0])
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 404)

        # Test joining a tournament
        async_to_sync(self.tournament.add_player)(self.users[0])
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], self.tournament.id)
        self.assertEqual(data["isHost"], True)
        self.assertEqual(data["isStarted"], False)

        # Test leaving a tournament
        response = self.client.delete(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.tournament.players.count(), 0)

    def test_start_tournament(self):
        url = reverse(
            "tournament_detail", kwargs={"tournament_id": self.tournament.id + 1}
        )
        self.assertEqual(Tournament.objects.count(), 1)

        response = self.client.post(url)
        self.assertEqual(response.status_code, 401)

        token, _ = generate_user_token(self.users[1])
        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 404)

        url = reverse("tournament_detail", kwargs={"tournament_id": self.tournament.id})
        async_to_sync(self.tournament.set_host)(self.users[0])
        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 401)

        token, _ = generate_user_token(self.users[0])
        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 400)
        async_to_sync(self.tournament.add_player)(self.users[1])
        async_to_sync(self.tournament.add_player)(self.users[2])
        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Tournament.objects.filter(is_playing=True).count(), 1)
        self.assertEqual(GameRoom.objects.filter(tournament=self.tournament).count(), 2)

    def test_join_tournament(self):
        url = reverse("join_tournament", kwargs={"tournament_id": self.tournament.id})
        token, _ = generate_user_token(self.users[0])
        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(response.status_code, 400)

    def test_add_player(self):
        url = reverse("add_player_to_tournament")
        self.assertEqual(self.tournament.players.count(), 0)
        payload = {"username": self.users[0].username}

        response = self.client.post(
            url,
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

        token, _ = generate_user_token(self.users[0])
        response = self.client.post(
            url,
            payload,
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )
        self.assertTrue(response.json().get("success"))
        self.assertEqual(self.tournament.players.count(), 1)

    def test_tournament_detail(self):
        async_to_sync(self.add_players)(count=4)
        async_to_sync(self.tournament.set_host)(self.users[0])
        async_to_sync(self.tournament.start_tournament)()

        url = reverse("tournament_detail", kwargs={"tournament_id": self.tournament.id})
        token, _ = generate_user_token(self.users[0])
        response = self.client.get(url, HTTP_AUTHORIZATION=f"Bearer {token}")
        print(f"{response.json()=}")
        expected = {
            "id": self.tournament.id,
            "size": 4,
            "bracket": [
                {
                    "finished": False,
                    "players": [
                        {
                            "id": self.users[0].pk,
                            "name": "test1",
                            "score": 0,
                            "isWinner": False,
                        },
                        {
                            "id": self.users[2].pk,
                            "name": "test3",
                            "score": 0,
                            "isWinner": False,
                        },
                    ],
                },
                {
                    "finished": False,
                    "players": [
                        {
                            "id": self.users[1].pk,
                            "name": "test2",
                            "score": 0,
                            "isWinner": False,
                        },
                        {
                            "id": self.users[3].pk,
                            "name": "test4",
                            "score": 0,
                            "isWinner": False,
                        },
                    ],
                },
                {},
            ],
            "players": [
                {
                    "playerName": "test1",
                    "playerId": self.users[0].pk,
                    "avatar": "uploads/avatars/42_Logo.png",
                    "status": "ingame",
                },
                {
                    "playerName": "test2",
                    "playerId": self.users[1].pk,
                    "avatar": "uploads/avatars/42_Logo.png",
                    "status": "ingame",
                },
                {
                    "playerName": "test3",
                    "playerId": self.users[2].pk,
                    "avatar": "uploads/avatars/42_Logo.png",
                    "status": "ingame",
                },
                {
                    "playerName": "test4",
                    "playerId": self.users[3].pk,
                    "avatar": "uploads/avatars/42_Logo.png",
                    "status": "ingame",
                },
            ],
        }
        self.assertEqual(response.status_code, 200)
        self.assertDictEqual(response.json(), expected)

    async def test_play_tournament(self):
        self.assertFalse(await self.tournament.start_tournament())
        await self.add_players(count=3)
        self.assertTrue(await self.tournament.start_tournament())
        self.assertTrue(self.tournament.is_active)
        self.assertEqual(await self.tournament.get_current_round(), 1)
        games = await self.tournament.get_games(level=1)
        self.assertEqual(len(games), 2)
        players = await games[0].get_players()
        self.assertEqual(players[0].get("name"), "test1")
        self.assertEqual(players[1].get("name"), "test3")
        players = [player async for player in TournamentPlayer.objects.all()]
        self.assertEqual(len(await games[1].get_players()), 1)
        self.assertTrue(games[1].is_finished)
        self.assertFalse(await self.tournament.check_round_end())

        expected = [
            {
                "finished": False,
                "players": [
                    {
                        "id": self.users[0].pk,
                        "name": "test1",
                        "score": 0,
                        "isWinner": False,
                    },
                    {
                        "id": self.users[2].pk,
                        "name": "test3",
                        "score": 0,
                        "isWinner": False,
                    },
                ],
            },
            {
                "finished": True,
                "players": [
                    {
                        "id": self.users[1].pk,
                        "name": "test2",
                        "score": 0,
                        "isWinner": True,
                    },
                    {},
                ],
            },
            {},
        ]
        bracket = await self.tournament.bracket()
        self.assertCountEqual(bracket, expected)

        player = await GamePlayer.objects.aget(player_id=self.users[0].pk)
        await games[0].victory(player.session_id)
        self.assertEqual(await self.tournament.get_current_round(), 2)

        games = await self.tournament.get_games(level=2, is_active=True)
        self.assertEqual(len(games), 1)
        players = await games[0].get_players()
        self.assertEqual(players[0].get("name"), "test1")
        self.assertEqual(players[1].get("name"), "test2")
        self.assertFalse(await self.tournament.check_round_end())
        await games[0].victory(players[0].get("player_id"))
        await self.tournament.arefresh_from_db()
        self.assertTrue(self.tournament.is_finished)
        self.assertEqual(
            (await self.tournament.get_winner()).username,
            "test1",
        )

    # TODO: Test tournament actions when tournament is ongoing
