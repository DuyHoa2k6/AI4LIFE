"""Bounded HEAD-only redirect checks. No proxies, cookies, body, JS or second DNS lookup."""
import asyncio
import http.client
import ipaddress
import socket
import ssl
import threading
import time
from urllib.parse import urljoin, urlunsplit
from .schemas import UrlNetworkCheck, RedirectHop, UrlSignal
from .settings import get_setting
from .urls import analyze_urls, collect, parse

MAX_URLS = 3
MAX_REDIRECTS = 3
BUDGET = 6.0
SLOTS = threading.BoundedSemaphore(8)
REDIRECTS = {301,302,303,307,308}
MODEL_API_HOSTS={'generativelanguage.googleapis.com','api.openai.com','api.anthropic.com',
                 'api.mistral.ai','api.cohere.ai','api.cohere.com'}


class Blocked(Exception):
    pass


def public_ip(value):
    if '%' in value:return False
    ip = ipaddress.ip_address(value.split('%')[0])
    # Block transition mechanisms as well as private, loopback, reserved, metadata.
    return (ip.is_global and not ip.is_multicast and not ip.is_reserved
            and not (isinstance(ip,ipaddress.IPv6Address) and
                     (ip.ipv4_mapped is not None or ip.sixtofour is not None or ip.teredo is not None)))


def target(value):
    if len(value)>2048:raise Blocked('url_too_long')
    p,host,_,registered,_,safe=parse(value)
    if host in MODEL_API_HOSTS:raise Blocked('model_service_not_allowed')
    if p.username is not None or p.password is not None:raise Blocked('credentials_in_url')
    if (p.port or (443 if p.scheme=='https' else 80)) not in (80,443):raise Blocked('port_not_allowed')
    if host=='localhost' or host.endswith(('.localhost','.local','.internal','.home','.invalid','.test','.example','.onion')):
        raise Blocked('non_public_hostname')
    path=p.path or '/'
    # Percent-encode Unicode path/query; preserve already encoded bytes, never fragment.
    from urllib.parse import quote
    normalized=urlunsplit((p.scheme,('['+host+']' if ':' in host else host)+((':'+str(p.port)) if p.port else ''),
                          quote(path,safe="/%:@!$&'()*+,;=-._~"),quote(p.query,safe="%/:?@!$&'()*+,;=-._~"),''))
    return p,host,registered,safe,normalized


def resolve_public(host,port):
    # Validate every answer, including mixed public/private answers. Connect only to a checked IP.
    addresses=socket.getaddrinfo(host,port,type=socket.SOCK_STREAM)
    if not addresses or any(not public_ip(a[4][0]) for a in addresses):raise Blocked('non_public_address')
    return addresses[0][4][0]


class PinnedConnection(http.client.HTTPConnection):
    def __init__(self,host,port,address,secure,timeout):
        super().__init__(host,port,timeout=timeout)
        self.address,self.secure=address,secure

    def connect(self):
        # create_connection gets an IP literal: DNS cannot change after the safety check.
        self.sock=socket.create_connection((self.address,self.port),self.timeout)
        if self.secure:
            try:self.sock=ssl.create_default_context().wrap_socket(self.sock,server_hostname=self.host)
            except BaseException:
                self.sock.close()
                raise


def head(value,deadline):
    p,host,_,_,normalized=target(value)
    port=p.port or (443 if p.scheme=='https' else 80)
    address=resolve_public(host,port)
    remaining=deadline-time.monotonic()
    if remaining<=0:raise TimeoutError()
    conn=PinnedConnection(host,port,address,p.scheme=='https',min(2.0,remaining))
    q=target(normalized)[0]
    def interrupt():
        sock=conn.sock
        if sock is not None:
            try:sock.shutdown(socket.SHUT_RDWR)
            except OSError:pass
        conn.close()
    timer=threading.Timer(remaining,interrupt);timer.daemon=True;timer.start()
    try:
        conn.request('HEAD',(q.path or '/')+('?' + q.query if q.query else ''),headers={
            'User-Agent':'ScamShield-LinkCheck/1.0','Accept':'*/*','Connection':'close'})
        response=conn.getresponse()
        # Do not read the body or retain headers other than Location. No credential forwarding.
        try:return response.status,response.getheader('Location')
        finally:response.close()
    finally:
        timer.cancel();conn.close()


def check_redirects(value):
    started=time.monotonic()
    result=UrlNetworkCheck()
    if not SLOTS.acquire(blocking=False):return UrlNetworkCheck(status='deferred',reason='checker_busy')
    try:
        deadline=started+BUDGET
        current=value;seen=set()
        for index in range(MAX_REDIRECTS+1):
            if time.monotonic()>=deadline:raise TimeoutError()
            _,host,registered,safe,normalized=target(current)
            if normalized in seen:
                result.status='redirect_loop';result.reason='redirect_loop';break
            seen.add(normalized)
            status,location=head(normalized,deadline)
            result.hops.append(RedirectHop(display_url=safe,http_status=status))
            if status in REDIRECTS:
                if not location:
                    result.status='error';result.reason='redirect_without_location';break
                # Validate the target before following it, even at the hop limit.
                current=urljoin(normalized,location)
                target(current)
                if index==MAX_REDIRECTS:
                    result.status='redirect_limit';result.reason='redirect_limit';break
                continue
            result.final_url=safe;result.final_hostname=host
            result.final_registered_domain=registered;result.final_http_status=status
            result.reachable=True
            result.status='unsupported' if status in (405,501) else 'checked'
            if result.status=='unsupported':result.reason='head_not_supported'
            break
    except Blocked as e:result.status='blocked';result.reason=str(e)
    except (TimeoutError,socket.timeout):result.status='timeout';result.reason='network_timeout'
    except socket.gaierror:result.status='error';result.reason='dns_failed'
    except (ValueError,UnicodeError):result.status='blocked';result.reason='invalid_url'
    except (OSError,http.client.HTTPException):result.status='error';result.reason='connection_or_tls_failed'
    finally:
        result.elapsed_ms=(time.monotonic()-started)*1000
        SLOTS.release()
    return result


async def inspect_urls(request,network=True):
    analyses=await asyncio.to_thread(analyze_urls,request)
    if not network or get_setting('SCAMSHIELD_URL_NETWORK_ENABLED','1')!='1':
        for a in analyses:a.network.status='disabled'
        return analyses
    records={r['id']:r for r in collect(request)}
    async def work(a,index):
        if a.status!='parsed':
            a.network=UrlNetworkCheck(status='blocked',reason='invalid_url');return
        if index>=MAX_URLS:
            a.network=UrlNetworkCheck(status='deferred',reason='per_request_limit');return
        try:a.network=await asyncio.wait_for(asyncio.to_thread(check_redirects,records[a.link_id]['url']),BUDGET+.25)
        except asyncio.TimeoutError:a.network=UrlNetworkCheck(status='timeout',reason='network_budget',elapsed_ms=(BUDGET+.25)*1000)
        n=a.network
        if n.status!='checked' or not n.final_url:return
        if len(n.hops)>1 and (n.final_registered_domain or n.final_hostname)!=(a.registered_domain or a.hostname):
            a.signals.append(UrlSignal(code='redirect_domain_change',level='info',detail='Liên kết chuyển sang miền '+n.final_hostname+'; chuyển miền không tự chứng minh lừa đảo.'))
        if any(h.display_url.startswith('https:') and k.display_url.startswith('http:') for h,k in zip(n.hops,n.hops[1:])):
            a.signals.append(UrlSignal(code='https_downgrade',level='review',detail='Chuỗi chuyển hướng có bước từ HTTPS xuống HTTP.'))
        # Reuse structural checks on the observed final origin; never give the model raw Location.
        from .schemas import AnalyzeRequest
        final_request=AnalyzeRequest(text='Đích liên kết',links=[{'id':a.link_id,'message_id':'m1','url':n.final_url}])
        final_analysis=analyze_urls(final_request)[0]
        existing={s.code for s in a.signals}
        for signal in final_analysis.signals:
            if signal.code not in existing:
                a.signals.append(signal.model_copy(update={'detail':'Đích sau chuyển hướng: '+signal.detail}))
    await asyncio.gather(*(work(a,i) for i,a in enumerate(analyses)))
    return analyses
