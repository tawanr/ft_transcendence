from django.contrib.auth.models import User
from django.test import TestCase

from gameplay.models import GamePlayer, GameRoom, Tournament


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

    async def test_add_player(self):
        self.assertFalse(await self.tournament.is_ready)
        await self.tournament.add_player(self.users[0])
        await self.tournament.add_player(self.users[1])
        self.assertFalse(await self.tournament.is_ready)
        await self.tournament.add_player(self.users[2])
        self.assertTrue(await self.tournament.is_ready)
        self.assertEqual(await self.tournament.players.acount(), 3)

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
                        "is_winner": False,
                    },
                    {
                        "id": self.users[2].pk,
                        "name": "test3",
                        "score": 0,
                        "is_winner": False,
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
                        "is_winner": True,
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
        self.assertTrue(await self.tournament.check_round_end())
        await self.tournament.start_new_round()

        games = await self.tournament.get_games(level=2, is_active=True)
        self.assertEqual(len(games), 1)
        players = await games[0].get_players()
        self.assertEqual(players[0].get("name"), "test1")
        self.assertEqual(players[1].get("name"), "test2")
        self.assertFalse(await self.tournament.check_round_end())
        await games[0].victory(players[0].get("player_id"))
        self.assertTrue(await self.tournament.check_round_end())
        await self.tournament.start_new_round()
        self.assertTrue(self.tournament.is_finished)
        self.assertEqual(
            (await self.tournament.get_winner()).username,
            "test1",
        )
