"""Check real notification payload construction without contacting Discord."""
import ast
import datetime
import logging
import os
from pathlib import Path
from types import SimpleNamespace
from typing import NotRequired, TypedDict
import unittest


class BackupNotificationTests(unittest.TestCase):
    def setUp(self):
        self.sent=[]
        def post(url,**kwargs):
            self.sent.append((url,kwargs))
            return SimpleNamespace(raise_for_status=lambda:None)
        env={'TypedDict':TypedDict,'NotRequired':NotRequired,'datetime':datetime,'os':os,
             'requests':SimpleNamespace(post=post),'logger':logging.getLogger('notification-test'),
             '_ALLOWED_DISCORD_HOSTS':frozenset({'discord.com'})}
        source=Path(__file__).resolve().parents[1]/'www/admin/backup.py'
        tree=ast.parse(source.read_text(encoding='utf-8'))
        names={'_DiscordField','_DiscordEmbed','_assert_discord_webhook','DiscordNotifier'}
        nodes=[node for node in tree.body
               if isinstance(node,(ast.ClassDef,ast.FunctionDef)) and node.name in names]
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'actual-notification','exec'),env)
        self.notifier=env['DiscordNotifier']('https://discord.com/api/webhooks/test/token')

    def test_optional_fields_preserve_notification_payload(self):
        self.assertTrue(self.notifier.send_notification('Backup','Complete'))
        url,request=self.sent[0]
        self.assertEqual(url,self.notifier.webhook_url)
        self.assertEqual(request['timeout'],10)
        embed=request['json']['embeds'][0]
        self.assertEqual(embed['title'],'Backup')
        self.assertEqual(embed['description'],'Complete')
        self.assertEqual(embed['color'],0x28a745)
        self.assertNotIn('fields',embed)

    def test_fields_and_failure_color_keep_the_existing_json_shape(self):
        fields=[{'name':'Archive','value':'example.tar.gz','inline':True}]
        self.assertTrue(self.notifier.send_notification('Backup','Failed',False,fields))
        embed=self.sent[0][1]['json']['embeds'][0]
        self.assertEqual(embed['fields'],fields)
        self.assertEqual(embed['color'],0xdc3545)


if __name__=='__main__':
    unittest.main()
