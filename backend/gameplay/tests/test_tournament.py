from django.test import TestCase
from django.contrib.auth.models import User

from gameplay.models import GameRoom, Tournament


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
        games = await self.tournament.get_games(level=1)
        self.assertEqual(len(games), 2)
        players = await games[0].get_players()
        self.assertEqual(players[0].get("name"), "test1")
        self.assertEqual(players[1].get("name"), "test2")
        self.assertEqual(len(await games[1].get_players()), 1)
        self.assertTrue(games[1].is_finished)
