"""Guard: SEO batch B1 — robots.txt allows the expanded AI crawler set."""
from django.test import TestCase

# The 10 crawlers added in B1, on top of the 6 already present.
NEW_AI_CRAWLERS = [
    'meta-externalagent',
    'CCBot',
    'Bytespider',
    'Amazonbot',
    'Claude-User',
    'ChatGPT-User',
    'DuckAssistBot',
    'YouBot',
    'Omgilibot',
    'Diffbot',
]


class RobotsAiCrawlerTests(TestCase):
    def test_all_new_ai_crawlers_are_allowed(self):
        resp = self.client.get('/robots.txt')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('text/plain', resp['Content-Type'])
        body = resp.content.decode()
        for agent in NEW_AI_CRAWLERS:
            self.assertIn(
                'User-agent: %s' % agent, body,
                'robots.txt must allow the %s AI crawler' % agent)
            # each allowed block must grant full access
            self.assertIn('User-agent: %s\nAllow: /' % agent, body)

    def test_existing_ai_crawlers_still_present(self):
        resp = self.client.get('/robots.txt')
        body = resp.content.decode()
        for agent in ('GPTBot', 'OAI-SearchBot', 'ClaudeBot',
                      'PerplexityBot', 'Google-Extended', 'Applebot-Extended'):
            self.assertIn('User-agent: %s' % agent, body)
