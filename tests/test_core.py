"""Проверки логики без сети. Запуск: uv run python -m unittest discover -s tests -v"""
import json
import time
import unittest
from datetime import timedelta
from pathlib import Path

from app import auth, bot, config, db, rates, services, telegram
from app.parser import parse_conversion, parse_entry

FIX = Path(__file__).parent / "fixtures"
# Выдуманный «бот» только для проверки подписи; настоящего значения здесь нет.
FAKE_BOT = "123456" + ":" + "sample"


def seed_rates():
    today = rates.today()
    for i in range(35):
        d = today - timedelta(days=i)
        for code, v in {"USD": 81.5, "EUR": 95.2, "CNY": 11.4, "USDT": 81.7, "BTC": 8_950_000, "AED": 22.19}.items():
            rates.save(code, d, v * (1 - i * 0.001))


class Base(unittest.TestCase):
    def setUp(self):
        db.connect(":memory:")
        seed_rates()
        self.user = services.ensure_user(111, "Арсений")


class ParserTests(unittest.TestCase):
    def test_expense(self):
        e = parse_entry("кофе 350")
        self.assertEqual((e["type"], e["amount"], e["currency"], e["category"]), ("exp", 350, "RUB", "food"))

    def test_income_plus(self):
        e = parse_entry("+120000 зарплата")
        self.assertEqual((e["type"], e["category"]), ("inc", "salary"))

    def test_thousands_and_cash(self):
        e = parse_entry("такси 1,5к нал")
        self.assertEqual((e["amount"], e["category"], e["account_kind"]), (1500, "transport", "cash"))

    def test_foreign(self):
        e = parse_entry("20$ сувенир")
        self.assertEqual((e["amount"], e["currency"], e["note"]), (20, "USD", "сувенир"))

    def test_spaces_in_number(self):
        self.assertEqual(parse_entry("1 500 продукты")["amount"], 1500)

    def test_no_amount(self):
        self.assertIsNone(parse_entry("привет"))
        self.assertIsNone(parse_entry("/start"))

    def test_conversion(self):
        self.assertEqual(parse_conversion("5000 руб в евро"), (5000, "RUB", "EUR"))
        self.assertEqual(parse_conversion("100$"), (100, "USD", "RUB"))


class AuthTests(unittest.TestCase):
    def signed(self, user, age=0, bot_id=FAKE_BOT):
        return auth.sign_init_data({"auth_date": str(int(time.time()) - age), "user": json.dumps(user)}, bot_id)

    def test_valid_signature(self):
        self.assertEqual(auth.check_init_data(self.signed({"id": 42, "first_name": "A"}), FAKE_BOT)["id"], 42)

    def test_tampered(self):
        self.assertIsNone(auth.check_init_data(self.signed({"id": 42}).replace("42", "43"), FAKE_BOT))

    def test_other_bot(self):
        self.assertIsNone(auth.check_init_data(self.signed({"id": 42}), "999" + ":" + "other"))

    def test_expired(self):
        self.assertIsNone(auth.check_init_data(self.signed({"id": 1}, age=3 * 86400), FAKE_BOT))


class RatesParseTests(unittest.TestCase):
    def test_cbr_daily(self):
        r = rates.parse_cbr_daily((FIX / "cbr_daily.xml").read_bytes())
        self.assertAlmostEqual(r["USD"], 81.5012, places=4)
        self.assertAlmostEqual(r["CNY"], 11.4012, places=4)
        self.assertAlmostEqual(r["AED"], 22.1901, places=4)
        self.assertNotIn("KZT", r)

    def test_cbr_dynamic(self):
        r = rates.parse_cbr_dynamic((FIX / "cbr_dynamic.xml").read_bytes())
        self.assertEqual(len(r), 2)
        self.assertAlmostEqual(r[0][1], 80.9, places=3)

    def test_coingecko(self):
        r = rates.parse_cg_simple(b'{"tether":{"rub":81.7},"bitcoin":{"rub":8950000}}')
        self.assertEqual(r, {"USDT": 81.7, "BTC": 8950000.0})
        ch = rates.parse_cg_chart(b'{"prices":[[1727740800000,80.1],[1727827200000,81.2]]}')
        self.assertEqual(len(ch), 2)


class ServiceTests(Base):
    def test_defaults(self):
        self.assertEqual([a["name"] for a in services.accounts(111)], ["Т-Банк", "Наличные", "Крипто"])
        self.assertTrue(self.user["api_key"].startswith("dk_"))

    def test_add_and_balance(self):
        services.set_balance(111, services.accounts(111)[0]["id"], 50000)
        t = services.add_transaction(111, "exp", 350, "RUB", "food")
        self.assertEqual(t["cat_key"], "food")
        h = services.home(self.user)
        self.assertAlmostEqual(h["accounts"][0]["balance"], 49650)
        self.assertEqual(h["categories"][0]["key"], "food")
        self.assertEqual(len(h["accounts"][0]["series"]), 30)

    def test_adjustment_not_counted_as_spending(self):
        services.set_balance(111, services.accounts(111)[0]["id"], 1000)
        services.set_balance(111, services.accounts(111)[0]["id"], 400)
        self.assertEqual(services.stats(self.user)["spent"], 0)

    def test_foreign_currency_converted_at_day_rate(self):
        t = services.add_transaction(111, "exp", 20, "USD", "shop")
        self.assertAlmostEqual(t["amount_rub"], 20 * rates.rate("USD"), places=4)
        self.assertAlmostEqual(t["amount_acc"], -t["amount_rub"], places=4)

    def test_crypto_goes_to_crypto_account(self):
        t = services.add_transaction(111, "inc", 100, "USDT", "other_inc")
        self.assertEqual(t["account_name"], "Крипто")
        self.assertAlmostEqual(t["amount_acc"], 100)

    def test_old_records_keep_their_rate(self):
        t = services.add_transaction(111, "exp", 10, "USD", "shop")
        before = t["amount_rub"]
        rates.save("USD", rates.today(), 200.0)
        self.assertAlmostEqual(services.transaction(111, t["id"])["amount_rub"], before)

    def test_limit_and_text(self):
        services.set_limit(111, 10000)
        t = services.add_transaction(111, "exp", 2000, "RUB", "food")
        text = services.recorded_text(self.user, t)
        self.assertIn("Записано −2 000 ₽ · Еда", text)
        self.assertIn("осталось 8 000 ₽", text)

    def test_validation(self):
        with self.assertRaises(services.ValidationError):
            services.add_transaction(111, "exp", -5)
        with self.assertRaises(services.ValidationError):
            services.add_transaction(111, "exp", 5, "XYZ")

    def test_other_users_data_is_hidden(self):
        services.ensure_user(222, "Чужой")
        t = services.add_transaction(222, "exp", 100, category="food")
        with self.assertRaises(services.ValidationError):
            services.delete_transaction(111, t["id"])
        with self.assertRaises(services.ValidationError):
            services.add_transaction(111, "exp", 100, account_id=services.accounts(222)[0]["id"])

    def test_undo(self):
        services.add_transaction(111, "exp", 100, category="food")
        services.add_transaction(111, "exp", 200, category="food")
        self.assertEqual(services.undo_last(111)["amount"], 200)

    def test_stats_ranges(self):
        services.add_transaction(111, "exp", 500, category="food")
        for rng in ("14d", "3m"):
            s = services.stats(self.user, rng)
            self.assertEqual(sum(b["ghost"] for b in s["bars"]), 0)
        s = services.stats(self.user, "1m")
        self.assertEqual(len(s["bars"]), services.month_bounds()[1].day)
        self.assertEqual(s["shares"][0]["key"], "food")

    def test_rates_view(self):
        v = services.rates_view()
        self.assertEqual([x["code"] for x in v], rates.ALL)
        self.assertEqual(len(v[0]["series"]), 30)


class BotTests(Base):
    def setUp(self):
        super().setUp()
        telegram.SENT = []

    def tearDown(self):
        telegram.SENT = None

    def msg(self, text):
        bot.handle_update({"message": {"chat": {"id": 111, "type": "private"}, "from": {"id": 111, "first_name": "Арсений"},
                                       "text": text}})
        return telegram.SENT[-1][1]

    def test_record_and_undo_button(self):
        sent = self.msg("кофе 350")
        self.assertIn("Записано −350", sent["text"])
        cb = sent["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
        bot.handle_update({"callback_query": {"id": "1", "data": cb, "from": {"id": 111},
                                              "message": {"chat": {"id": 111}, "message_id": 5}}})
        self.assertEqual(services.recent(111), [])

    def test_conversion_question_is_not_recorded(self):
        sent = self.msg("100 usd")
        self.assertIn("=", sent["text"])
        self.assertEqual(services.recent(111), [])

    def test_commands(self):
        self.assertIn("DELTA", self.msg("/start")["text"])
        self.assertIn("Всего", self.msg("/balance")["text"])
        self.assertIn("dk_", self.msg("/key")["text"])
        self.assertIn("Лимит на месяц", self.msg("/limit 100000")["text"])
        self.assertIn("=", self.msg("/rate 100 eur")["text"])

    def test_key_message_links_guide_with_key_after_hash(self):
        old = config.PUBLIC_URL
        config.PUBLIC_URL = "https://delta.example"
        try:
            text = self.msg("/key")["text"]
        finally:
            config.PUBLIC_URL = old
        key = services.get_user(111)["api_key"]
        self.assertIn(f"https://delta.example/ios#k={key}", text)


class Texts(Base):
    def test_totals_are_whole_rubles(self):
        services.set_limit(111, 100000)
        t = services.add_transaction(111, "exp", "333.33", category="food")
        self.assertIn("осталось 99", services.recorded_text(self.user, t))
        self.assertNotIn(",", services.recorded_text(self.user, t).split("\n")[1])
        self.assertNotRegex(services.balance_text(self.user), r"\d,\d\d ₽")


class Pages(unittest.TestCase):
    def test_ios_guide_page_is_built_from_doc(self):
        page = (Path(__file__).parent.parent / "webapp" / "ios.html").read_text(encoding="utf-8")
        self.assertIn("Касание задней панели", page)
        self.assertIn('class="key"', page)


if __name__ == "__main__":
    unittest.main()
