from django.test import TestCase, Client
from django.contrib.auth.models import User, Group
from django.urls import reverse
from catalog.models import Game, BorrowRequest, BorrowedGame


class LibrarySystemTests(TestCase):
    def setUp(self):
        self.patron_group, _ = Group.objects.get_or_create(name="Patron")
        self.librarian_group, _ = Group.objects.get_or_create(name="Librarian")

        self.patron = User.objects.create_user(username="patron1", password="pass")
        self.librarian = User.objects.create_user(username="librarian1", password="pass")
        self.patron.groups.add(self.patron_group)
        self.librarian.groups.add(self.librarian_group)

        self.game = Game.objects.create(title="Tetris", platform="NES", genre="Puzzle", available=True)
        self.client = Client()

    def test_patron_borrow_request(self):
        self.client.login(username="patron1", password="pass")
        response = self.client.get(reverse("catalog:borrow_game", args=[self.game.id]), follow=True)
        self.assertContains(response, "Borrow request for Tetris submitted")
        self.assertEqual(BorrowRequest.objects.count(), 1)

    def test_librarian_approve_request(self):
        request = BorrowRequest.objects.create(user=self.patron, game=self.game)
        self.client.login(username="librarian1", password="pass")
        response = self.client.post(reverse("catalog:approve_borrow", args=[request.id]), follow=True)
        self.assertContains(response, "Librarian Dashboard")
        self.assertTrue(BorrowRequest.objects.get(id=request.id).approved)
        self.assertFalse(Game.objects.get(id=self.game.id).available)
        self.assertEqual(BorrowedGame.objects.filter(user=self.patron, game=self.game).count(), 1)

    def test_librarian_deny_request(self):
        request = BorrowRequest.objects.create(user=self.patron, game=self.game)
        self.client.login(username="librarian1", password="pass")
        response = self.client.post(reverse("catalog:deny_borrow", args=[request.id]), follow=True)
        self.assertContains(response, "Librarian Dashboard")
        self.assertTrue(BorrowRequest.objects.get(id=request.id).denied)

    def test_patron_dashboard_view(self):
        self.client.login(username="patron1", password="pass")
        response = self.client.get(reverse("catalog:patron_dashboard"))
        self.assertContains(response, "Patron Dashboard")

    def test_librarian_dashboard_view(self):
        self.client.login(username="librarian1", password="pass")
        response = self.client.get(reverse("catalog:librarian_dashboard"))
        self.assertContains(response, "Librarian Dashboard")

    def test_game_list_view(self):
        self.client.login(username="patron1", password="pass")
        response = self.client.get(reverse("catalog:game_list"))
        self.assertContains(response, "Tetris")
