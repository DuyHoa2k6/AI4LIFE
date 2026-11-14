import asyncio
import os
import socket
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from backend import url_network as net
from backend.schemas import AnalyzeRequest, UrlNetworkCheck, RedirectHop


class UrlNetworkTests(unittest.TestCase):
    def test_model_api_domains_are_not_contacted_even_as_input_urls(self):
        for host in net.MODEL_API_HOSTS:
            with self.subTest(host=host),patch.object(net,'head') as opened:
                result=net.check_redirects('https://'+host+'/v1/test')
                self.assertEqual(result.status,'blocked')
                self.assertEqual(result.reason,'model_service_not_allowed');opened.assert_not_called()

    def test_non_public_and_transition_ips_blocked(self):
        for ip in ['127.0.0.1','10.0.0.1','169.254.169.254','0.0.0.0','192.168.1.1',
                   '224.0.0.1','::1','fc00::1','fe80::1','::ffff:8.8.8.8','2002:0808:0808::1']:
            with self.subTest(ip=ip):self.assertFalse(net.public_ip(ip))
        self.assertTrue(net.public_ip('8.8.8.8'))

    def test_mixed_public_private_dns_rejected(self):
        rows=[(2,1,6,'',('8.8.8.8',443)),(2,1,6,'',('127.0.0.1',443))]
        with patch.object(socket,'getaddrinfo',return_value=rows):
            with self.assertRaises(net.Blocked):net.resolve_public('example.com',443)

    def test_credentials_ports_and_special_names_never_opened(self):
        for url in ['file:///etc/passwd','https://name:secret@example.com',
                    'https://example.com:8080','http://localhost','https://a.local',
                    'https://xacthuc-sinhvien.invalid/kiem-tra','https://a.test',
                    'https://example.com/\r\nInjected: value']:
            with self.subTest(url=url),patch.object(net,'head') as opened:
                result=net.check_redirects(url)
                self.assertEqual(result.status,'blocked');opened.assert_not_called()

    def test_relative_redirect_and_secret_redaction(self):
        with patch.object(net,'head',side_effect=[(302,'/final?token=SECRET'),(200,None)]) as h:
            r=net.check_redirects('https://example.com/start?token=SECRET#FRAGMENT')
        self.assertEqual(r.status,'checked');self.assertEqual(len(r.hops),2)
        self.assertEqual(h.call_args_list[1].args[0],'https://example.com/final?token=SECRET')
        self.assertNotIn('SECRET',r.model_dump_json());self.assertNotIn('FRAGMENT',r.model_dump_json())
        self.assertEqual(r.final_url,'https://example.com/')

    def test_redirect_loop_bounded(self):
        with patch.object(net,'head',return_value=(302,'/start')) as h:
            r=net.check_redirects('https://example.com/start')
        self.assertEqual(r.status,'redirect_loop');self.assertEqual(h.call_count,1)

    def test_max_four_head_requests(self):
        with patch.object(net,'head',side_effect=[(302,'/'+str(i)) for i in range(4)]) as h:
            r=net.check_redirects('https://example.com/start')
        self.assertEqual(r.status,'redirect_limit');self.assertEqual(h.call_count,4)
        self.assertIsNone(r.final_url)

    def test_404_is_response_not_scam_or_dns_proof(self):
        with patch.object(net,'head',return_value=(404,None)):
            r=net.check_redirects('https://example.com/missing')
        self.assertEqual(r.status,'checked');self.assertTrue(r.reachable)
        self.assertEqual(r.final_http_status,404)

    def test_head_unsupported_never_falls_back_to_get(self):
        with patch.object(net,'head',return_value=(405,None)) as h:
            r=net.check_redirects('https://example.com/')
        self.assertEqual(r.status,'unsupported');self.assertEqual(h.call_count,1)

    def test_timeout_dns_and_tls_failures_are_distinct_from_safe(self):
        for error,status in [(TimeoutError(),'timeout'),(socket.gaierror(),'error'),(OSError(),'error')]:
            with patch.object(net,'head',side_effect=error):
                r=net.check_redirects('https://example.com/')
            self.assertEqual(r.status,status);self.assertIsNone(r.reachable)

    def test_every_hop_dns_checked_before_connection(self):
        connections=[]
        class FakeConnection:
            def __init__(self,*args):connections.append(args)
            def request(self,*args,**kwargs):pass
            def getresponse(self):return SimpleNamespace(status=302,getheader=lambda _: 'http://127.0.0.1/private',close=lambda:None)
            def close(self):pass
        with patch.object(net,'resolve_public',side_effect=['8.8.8.8',net.Blocked('non_public_address')]) as dns,patch.object(net,'PinnedConnection',FakeConnection):
            r=net.check_redirects('https://example.com/')
        self.assertEqual(r.status,'blocked');self.assertEqual(dns.call_count,2)
        self.assertEqual(len(connections),1)

    def test_connection_uses_checked_ip_not_hostname(self):
        conn=net.PinnedConnection('example.com',80,'8.8.8.8',False,1)
        with patch.object(socket,'create_connection') as create:
            conn.connect()
        self.assertEqual(create.call_args.args[0],('8.8.8.8',80))

    def test_head_does_not_send_cookies_auth_or_read_body(self):
        with patch.object(net,'resolve_public',return_value='8.8.8.8'),patch.object(net,'PinnedConnection') as c:
            response=c.return_value.getresponse.return_value
            response.status=200;response.getheader.return_value=None
            net.head('https://example.com/a?b=1',time.monotonic()+5)
            request=c.return_value.request.call_args
            self.assertEqual(request.args,('HEAD','/a?b=1'))
            self.assertNotIn('Cookie',request.kwargs['headers']);self.assertNotIn('Authorization',request.kwargs['headers'])
            response.read.assert_not_called();c.return_value.close.assert_called_once()

    def test_disabled_never_touches_network(self):
        with patch.dict(os.environ,{'SCAMSHIELD_URL_NETWORK_ENABLED':'0'}),patch.object(net,'check_redirects') as c:
            r=asyncio.run(net.inspect_urls(AnalyzeRequest(text='https://example.com/')))
        c.assert_not_called();self.assertEqual(r[0].network.status,'disabled')

    def test_limit_three_links(self):
        req=AnalyzeRequest(text=' '.join('https://example.com/'+str(i) for i in range(4)))
        with patch.dict(os.environ,{'SCAMSHIELD_URL_NETWORK_ENABLED':'1'}),patch.object(net,'check_redirects',return_value=UrlNetworkCheck(status='error')) as c:
            r=asyncio.run(net.inspect_urls(req))
        self.assertEqual(c.call_count,3);self.assertEqual(r[-1].network.status,'deferred')

    def test_final_domain_signals_and_downgrade_available_for_review(self):
        n=UrlNetworkCheck(status='checked',hops=[RedirectHop(display_url='https://example.com/',http_status=302),
            RedirectHop(display_url='http://youtubee.com/',http_status=200)],final_url='http://youtubee.com/',
            final_hostname='youtubee.com',final_registered_domain='youtubee.com',final_http_status=200,reachable=True)
        with patch.dict(os.environ,{'SCAMSHIELD_URL_NETWORK_ENABLED':'1'}),patch.object(net,'check_redirects',return_value=n):
            r=asyncio.run(net.inspect_urls(AnalyzeRequest(text='https://example.com/')))
        codes={s.code for s in r[0].signals}
        self.assertTrue({'lookalike_reference_domain','redirect_domain_change','https_downgrade'}<=codes)

    def test_unknown_network_error_keeps_offline_results(self):
        with patch.dict(os.environ,{'SCAMSHIELD_URL_NETWORK_ENABLED':'1'}),patch.object(net,'check_redirects',return_value=UrlNetworkCheck(status='error')):
            r=asyncio.run(net.inspect_urls(AnalyzeRequest(text='https://youtubee.com/')))
        self.assertIn('lookalike_reference_domain',{s.code for s in r[0].signals})

