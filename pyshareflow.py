from datetime import datetime
from xml.utils import iso8601
import StringIO
import gzip
import httplib
import json
import mimetools
import mimetypes
import os.path
import re
import urllib
import urllib2
import uuid

VERSION=2
SERVER='api.zenbe.com'

# urllib2.install_opener(
#     urllib2.build_opener(
#         urllib2.ProxyHandler({'http': 'http://127.0.0.1:8080',
#                               'https': 'http://127.0.0.1:8080'})))


class Api(object):
    def __init__(self, user_domain, key, version=VERSION, use_ssl=False,
                 server=SERVER):
        self.requester = Requester(server, user_domain, key, version, use_ssl)

    @classmethod
    def get_auth_token(cls, username, password, user_domain):
        requester = Requester(SERVER, user_domain, use_ssl=True)
        response = requester.get_auth_token(username, password)
        if 'data' in response:
            return response['data']['auth_token']
        return None
        

##### User Methods #####

    def get_users(self, flow_id=None, offset=None, limit=50):
        query = None

        if flow_id:
            query = Query('flows')
            query.id = flow_id
            query.include = ['users']
        else:
            query = Query('users')
        
        if offset:
            query.offset = offset

        query.limit = limit

        response = self.requester.api_query(query)

        users = None

        if 'users' in response:
            users = [User.from_json(user) for user in response['users']]

        return users or []

    def get_user(self, user_id):
        query = Query('users')
        query.id = user_id

        response = self.requester.api_query(query)

        user = None

        if 'users' in response:
            user = [User.from_json(user) for user in response['users']][0]

        return user

    def remove_user(self, user_id, flow_id):
        update = Update('flows')
        update.id = flow_id
        update.remove_members = [user_id]

        response = self.requester.api_update(update)

##### Flow Methods #####

    def get_flows(self, 
                  limit=30,                   
                  order_by='created',
                  name=None,
                  offset=None):
        if order_by not in ['updated', 'created']:
            raise ValueError("order_by must be one of 'updated', 'created'")

        query = Query('flows')
        query.include = ['memberships','invitations']
        query.limit = min(limit, 100)
        query.order = '{0}_at desc'.format(order_by)

        if name:
            query.name = name

        if offset:
            query.offset = offset

        response = self.requester.api_query(query)

        return self._merge_flow_data(response)

    def get_flow_by_name(self, name):
        flows = self.get_flows(name=name)

        if len(flows) > 0:
            return flows[0]
        else:
            return None

    def create_flow(self, name):
        update = Update('flows')
        update.name = name
        update.id = str(uuid.uuid4())

        response = self.requester.api_update(update)

        return Flow.from_json(response['flows'][0])

    def update_flow_name(self, name, flow_id):
        update = Update('flows')
        update.name = name
        update.id = flow_id

        response = self.requester.api_update(update)

        return Flow.from_json(response['flows'][0])

    def delete_flow(self, flow_id):
        update = Update('flows')
        update.id = flow_id
        update._removed = True

        response = self.requester.api_update(update)

    def create_invitations(self, flow_id, invitees):
        if isinstance(invitees, str):
            invitees = [invitees]

        update = Update('flows')
        update.invite = invitees
        update.id = flow_id

        response = self.requester.api_update(update)

        return Flow.from_json(response['flows'][0])

    def delete_invitations(self, flow_id, invitees):
        if isinstance(invitees, str):
            invitees = [invitees]

        update = Update('flows')
        update.uninvite = invitees
        update.id = flow_id

        response = self.requester.api_update(update)

        return Flow.from_json(response['flows'][0])

##### Post Methods #####
        
    def get_posts(self, 
                  limit=30, 
                  include_comments=True, 
                  flow_id=None, 
                  order_by='created',
                  offset=None,
                  before=None,
                  after=None,
                  search_term=None):

        if order_by not in ['updated', 'created']:
            raise ValueError("order_by must be one of 'updated', 'created'")

        if offset and (before or after):
            raise InvalidRequest("offset cannot be specified with before or after param")

        query = Query('posts')
        query.order = '{0}_at desc'.format(order_by)
        query.limit = min(limit, 100)
        query.include = ['files']
        
        if offset:
            query.offset = max(offset, 0)

        if flow_id:
            query.flow_id = {'in': flow_id}

        if search_term:
            query.keywords = search_term

        if include_comments:
            query.include.append('comments')

        self._add_time_params(query, order_by, before, after)

        response = self.requester.api_query(query)

        return self._merge_post_data(response)

    def search(self,
               search_term,
               limit=30, 
               include_comments=True, 
               flow_id=None, 
               order_by='created',
               before=None,
               after=None):


        return self.get_posts(search_term=search_term,
                              limit=limit,
                              include_comments=include_comments,
                              flow_id=flow_id,
                              order_by=order_by,
                              before=before,
                              after=after)

    def post_files(self, file_paths, flow_id, comment=None):
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        if len(file_paths) == 0:
            raise ValueError("file_paths must not be empty")

        update = Update('posts')
        update.flow_id = flow_id
        update.id = str(uuid.uuid4())

        if comment:
            update.content = comment

        response = self.requester.api_update_with_files(update, file_paths)

    def add_files_to_post(self, file_paths, post_id):
        if isinstance(file_paths, str):
            file_paths = [file_paths]

        if len(file_paths) == 0:
            raise ValueError("file_paths must not be empty")

        update = Update('posts')
        update.id = post_id

        response = self.requester.api_update_with_files(update, file_paths)

    def create_post(self, flow_id, content):
        update = Update('posts')
        update.flow_id = flow_id
        update.content = content
        update.id = str(uuid.uuid4())

        response = self.requester.api_update(update)

        return Post.from_json(response['posts'][0])

    def update_post(self, post_id, content=None, file_paths=None):
        update = Update('posts')
        update.id = post_id

        if not (content or file_paths):
            raise ValueError("content or file_paths can't both be None")

        if content:
            update.content = content

        response = None

        if file_paths:
            if isinstance(file_paths, str):
                file_paths = [file_paths]
            response = self.requester.api_update_with_files(update, file_paths)
        else:
            response = self.requester.api_update(update)
            
        return Post.from_json(response['posts'][0])

    def delete_post(self, post_id):
        update = Update('posts')
        update.id = post_id
        update._removed = True

        response = self.requester.api_update(update)

##### Comment Methods #####

    def get_comments(self, post_id):
        query = Query('comments')
        query.post_id = post_id
        
        response = self.requester.api_query(query)
        
        comments = None

        if 'comments' in response:
            comments = [Comment.from_json(comment) for comment in response['comments']]

        return comments or []

    def create_comment(self, post_id, content):
        update = Update('comments')
        update.post_id = post_id
        update.id = str(uuid.uuid4())
        update.content = content

        response = self.requester.api_update(update)

        return Comment.from_json(response['comments'][0])

    def delete_comment(self, comment_id):
        update = Update('comments')
        update.id = comment_id
        update._removed = True

        response = self.requester.api_update(update)

##### Internal Methods #####

    def _add_time_params(self, query, order_by, before, after):
        # TODO Allow inclusive, exclusive
        time_param = {}

        if before:
            time_param.update({'<': iso8601.tostring(before)})

        if after:
            time_param.update({'>' : iso8601.tostring(after)})

        if len(time_param) > 0:
            if order_by == 'updated':
                query.updated_at = time_param
            else:
                query.created_at = time_param

    def _merge_flow_data(self, data):
        if len(data['flows']) == 0:
            return []

        # This list preserves server order requested by the user
        flows = [Flow.from_json(flow) for flow in data['flows']]
        # Index the flows to merge the data
        flows_idx = dict((flow.id, flow) for flow in flows)

        # Associate users with flows via memberships
        if 'memberships' in data:
            for m in data['memberships']:
                if m['administrator']:
                    flow = flows_idx[m['channel_id']]
                    flow.owner = m['user_id']
                         
        # Add invitations
        if 'invitations' in data:
            for i in data['invitations']:
                flow = flows_idx[i['channel_id']]
                flow.invitations.append(Invitation(i['id'], i['email_address']))
            
        return flows


    def _merge_post_data(self, data):
        if len(data['posts']) == 0:
            return []

        # This list preserves the server order requested by the user
        posts = [self._create_post(post) for post in data['posts']]
 
        files = None
        comments = None

        if 'files' in data:
            files = dict((file['id'], File.from_json(self.requester, file)) for file in data['files'])

        if 'comments' in data:
            comments = dict((comment['id'], Comment.from_json(comment)) for comment in data['comments'])
 
        for post in posts:
            if files:
                post.files = [files[id] for id in post.file_ids]

            if comments:
                post.comments = [comments[id] for id in post.reply_ids]


        return posts
        
    def _create_post(self, post_data):
        type = post_data['post_type']
        types = {
            'image': ImagePost,
            'file': FilePost,
            'video': VideoPost,
            'map': MapPost,
            'message': EmailPost,
            'html': HTMLPost,
            'event': EventPost,
            'comment': Post
            }

        if not type in types:
            return Post.from_json(post_data)

        return types[type].from_json(post_data)

class Query(dict):
    def __init__(self, entity):
        self.__dict__['entity'] = entity
        self['query'] = {entity : {}}

    def __getattr__(self, name):
        val = self['query'][self.__dict__['entity']].get(name)
        if not val:
            raise AttributeError("Invalid attribute: {0}".format(name))
        return val

    def __setattr__(self, name, val):
        self['query'][self.__dict__['entity']][name] = val


class Update(dict):
    def __init__(self, entity):
        self.__dict__['entity'] = entity
        self['data'] = {entity: [{}]}

    def __getattr__(self, name):
       val = self['data'][self.__dict__['entity']][0].get(name)
       if not val:
           raise AttributeError("Invalid attribute: {0}".format(name))
       return val

    def __setattr__(self, name, val):
        self['data'][self.__dict__['entity']][0][name] = val

class Requester(object):
    USER_AGENT='pyshareflow APIv{0}'.format(VERSION)

    def __init__(self, server, user_domain, key=None, version=VERSION, 
                 use_ssl=False):
        protocol = 'https' if use_ssl else 'http'         
        self.base_url = "{0}://{1}/{2}".format(protocol, server, user_domain)
        self.api_url = "{0}/shareflow/api/v{1}.json".format(self.base_url, version)
        self.auth_url = "{0}/shareflow/api/v{1}/auth.json".format(self.base_url, version)
        self.key = key

    def get_auth_token(self, username, password):
        return self._request({'login': username, 'password': password}, 
                             self.auth_url)

    def api_update(self, update, timeout=60):
        update['key'] = self.key
        return self._request(update, self.api_url, timeout)

    def api_update_with_files(self, update, file_paths, timeout=300):
        return self._request_with_files(update, file_paths, self.api_url,
                                        timeout)

    def api_query(self, query, timeout=60):
        query['key'] = self.key
        return self._request(query, self.api_url, timeout)

    def content_request(self, path, timeout=300):
        req = urllib2.Request(self.create_url(path), 
                              headers={'User-Agent': Requester.USER_AGENT,
                                       'Accept-Encoding': 'gzip'})
        
        response = urllib2.urlopen(req, timeout=timeout)
        return self._read_response(response)

    def create_url(self, path):
        return "{0}{1}?key={2}".format(self.base_url, path, self.key)

    def _request(self, params, url, timeout=60, requestobj=None):

        req = requestobj or urllib2.Request(url, json.dumps(params),
                                            {'User-Agent': Requester.USER_AGENT,
                                             'Accept-Encoding': 'gzip',
                                             'Accept': 'application/json',
                                             'Content-Type': 'application/json; charset=UTF-8'})
        try:
            response = urllib2.urlopen(req, timeout=timeout)
        except urllib2.HTTPError as error:
            self._check_error(error)
            raise error

        data = self._read_response(response)
            
        return data

    def _request_with_files(self, update, file_paths, url, timeout=300):

        boundary = mimetools.choose_boundary()
        crlf = '\r\n'
        tmp = []
        tmp.append('--' + boundary)
        tmp.append('Content-Disposition: form-data; name="key"')
        tmp.append('Content-Type: application/json; charset=UTF-8')
        tmp.append('')
        tmp.append(str(self.key))

        files = []
        
        for path in file_paths:
            id = 'file_' + str(uuid.uuid4())

            tmp.append('--' + boundary)
            tmp.append('Content-Disposition: form-data; name="{0}"; filename="{1}"'
                       .format(id, os.path.basename(path)))
            tmp.append('Content-Type: {0}'.format(
                    mimetypes.guess_type(path)[0] or 'application/octet-stream'))
            tmp.append('')
            tmp.append(open(path, 'r').read())

            files.append({'part_id': id})

        update.files = files
        tmp.append('--' + boundary)
        tmp.append('Content-Disposition: form-data; name="data"')
        tmp.append('Content-Type: application/json; charset=UTF-8')
        tmp.append('')
        tmp.append(json.dumps(update['data']))

        tmp.append('--' + boundary + '--')
        tmp.append('')
        
        body = crlf.join(tmp)
        content_type = 'multipart/form-data; boundary={0}'.format(boundary)

        request = urllib2.Request(url, body,
                                  {'User-Agent': Requester.USER_AGENT,
                                   'Accept-Encoding': 'gzip',
                                   'Accept': 'application/json',
                                   'Content-Type': content_type,
                                   'Content-Length': str(len(body))})

        return self._request(None, None, timeout=timeout, requestobj=request)
                       

    def _check_error(self, error):
        exception_map = { httplib.BAD_REQUEST : InvalidRequest,
                          httplib.FORBIDDEN : ResourceException,
                          httplib.INTERNAL_SERVER_ERROR : ServiceError }
        
        if error.code not in exception_map:
            return

        # Try to get the server message
        msg = None
        if error.info().getheader('Content-Type').find('application/json') != -1:
            data = self._read_response(error)
            msg = data.get('message') or error.message
        else:
            msg = error.message
        
        # Raise a custom exception
        raise exception_map[response.code](msg)

    def _read_response(self, response):
        fp = None
        if response.info().getheader('Content-Encoding') == 'gzip':
            fp = gzip.GzipFile(fileobj=StringIO.StringIO(response.read()))
        else:
            fp = response

        if response.info().getheader('Content-Type').find('application/json') != -1:
            return json.load(fp)
        else:
            return fp.read()

##### Model Classes #####        

class Flow(object):
    _VALID_ATTRIBUTES = set([
            'id',
            'name',
            'email_address',
            'created_at',
            'updated_at',
            'default_channel',
            'owner_name',
            'quota_precentage',
            'quota_count',
            'rss_url'
            ])
    def __init__(self,
                 id=None, 
                 name=None, 
                 email_address=None, 
                 created_at=None,
                 updated_at=None, 
                 default_channel=False, 
                 owner_name=None, 
                 quota_percentage=0.0, 
                 quota_count=0, 
                 rss_url=None):
        self.id = id
        self.name = name
        self.email_address = email_address
        self.created_at = iso8601.parse(created_at) if created_at else None
        self.updated_at = iso8601.parse(updated_at) if updated_at else None
        self.is_default = default_channel
        self.owner_name = owner_name
        self.quota_percentage = quota_percentage
        self.quota_count = int(quota_count)
        self.rss_url = rss_url
        self.invitations = list()
        self.owner_id = None
                     
    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.created_at < other.created_at

    def __gt__(self, other):
        return self.created_at > other.created_at

    def __str__(self):
        return "Flow[{0.id}]: {0.name}".format(self)

    @classmethod
    def from_json(cls, data):
        return cls(**dict([(str(k),v) for k,v in data.iteritems() 
                           if k in cls._VALID_ATTRIBUTES]))
    

class User(object):
    _VALID_ATTRIBUTES = set([
            'avatar_url',
            'email',
            'first_name',
            'id',
            'last_name',
            'login',
            'online',
            'role',
            'time_zone'
            ])

    def __init__(self,
                 id=-1,
                 login=None,
                 first_name=None, 
                 last_name=None,
                 email=None, 
                 avatar_url=None,
                 online=False,
                 role=None,
                 time_zone=None):
        self.id = id
        self.login = login
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.avatar_url = avatar_url
        self.is_online = online
        self.role = role
        self.time_zone = time_zone

    def __hash__(self):
        return self.id

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.last_name < other.last_name

    def __gt__(self, other):
        return self.last_name > other.last_name

    def __str__(self):
        return "User[{0.id}]: {0.first_name} {0.last_name} <{0.email}>".format(self)

    @classmethod
    def from_json(cls, data):
        return cls(**dict([(str(k),v) for k,v in data.iteritems() 
                           if k in cls._VALID_ATTRIBUTES]))


class Invitation(object):
    def __init__(self, id, email):
        self.id = id
        self.email = email

    def __hash__(self):
        return self.id.__hash__()

    def __str__(self):
        return "Invitation[{0.id}]: {0.email}".format(self)


class File(object):
    _VALID_ATTRIBUTES = set([
            'content_type',
            'created_at',
            'file_name',
            'file_size',
            'height',
            'id',
            'is_image',
            'post_id',
            'thumbnail_url',
            'meta_data',
            'url',
            'width'
            ])

    def __init__(self,
                 requester,
                 id=None,
                 file_name=None,
                 file_size=0, 
                 post_id=None,
                 content_type=None,
                 is_image=False, 
                 meta_data=None,
                 width=None,
                 height=None,
                 url=None,
                 thumbnail_url=None,
                 created_at=None,
                 updated_at=None
                 ):
        self.__requester = requester
        self.__url = url
        self.id = id
        self.file_name = file_name
        self.file_size = file_size
        self.post_id = post_id
        self.content_type = content_type
        self.is_image = is_image
        self.meta_data = None if meta_data is None else json.loads(meta_data)
        self.width = int(width) if width else None
        self.height = int(height) if height else None
        self.thumbnail_url = thumbnail_url
        self.created_at = iso8601.parse(created_at) if created_at else None
        self.updated_at = iso8601.parse(updated_at) if updated_at else None

    @property
    def url(self):
        return self.__requester.create_url(self.__url)

    def retrieve(self):
        return self.__requester.content_request(self.__url)

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.created_at < other.created_at

    def __gt__(self, other):
        return self.created_at > other.created_at

    def __str__(self):
        return "File[{0.id}]: {0.name}".format(self)


    @classmethod
    def from_json(cls, requester, data):
        return cls(requester, **dict([(str(k),v) for k,v in data.iteritems() 
                                      if k in cls._VALID_ATTRIBUTES]))

    
class Comment(object):
    _VALID_ATTRIBUTES = set([
            'content',
            'created_at',
            'flow_id',
            'flow_name',
            'reply_to',
            'id',
            'updated_at',
            'user_id'
            ])
    def __init__(self,
                 id=None,
                 flow_id=None,
                 flow_name=None,
                 reply_to=None,
                 content=None,
                 user_id=-1,
                 created_at=None,
                 updated_at=None):
        self.id = id
        self.flow_id = flow_id
        self.flow_name = flow_name
        self.reply_to = reply_to
        self.content = content
        self.created_at = iso8601.parse(created_at) if created_at else None
        self.updated_at = iso8601.parse(updated_at) if updated_at else None
        self.user_id = user_id

    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.created_at < other.created_at

    def __gt__(self, other):
        return self.created_at > other.created_at

    def __str__(self):
        return "Comment[{0.id}]: {0.user_id}".format(self)

    @classmethod
    def from_json(cls, data):
        return cls(**dict([(str(k),v) for k,v in data.iteritems() 
                           if k in cls._VALID_ATTRIBUTES]))

##### Posts #####

class Post(object):
    _VALID_ATTRIBUTES = set([
            'content',
            'created_at',
            'flow_id',
            'flow_name',
            'id',
            'post_type',
            'reply_ids',
            'file_ids',
            'star',
            'updated_at',
            'user_id'
            ])

    def __init__(self,
                 id=None,
                 flow_id=None,
                 flow_name=None,
                 post_type=None,
                 reply_ids=None,
                 file_ids=None,
                 user_id=-1,
                 content=None,
                 star=None,
                 created_at=None,
                 updated_at=None):
        self.id = id
        self.flow_id = flow_id
        self.flow_name = flow_name
        self.post_type = post_type
        self.content = content
        self.star = star
        self.created_at = iso8601.parse(created_at) if created_at else None
        self.updated_at = iso8601.parse(updated_at) if updated_at else None
        self.reply_ids = reply_ids or []
        self.file_ids = file_ids or []
        self.user_id = user_id

        self.files = list()
        self.comments = list()

    def is_map(self):
        return False

    def is_email(self):
        return False

    def is_event(self):
        return False

    def is_file(self):
        return False

    def is_image(self):
        return False

    def is_video(self):
        return False

    def is_html(self):
        return False

    def is_event(self):
        return False
                 
    def __hash__(self):
        return self.id.__hash__()

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.created_at < other.created_at

    def __gt__(self, other):
        return self.created_at > other.created_at

    def __str__(self):
        return "Post[{0.id}]: {0.post_type} {0.user_id}".format(self)

    @classmethod
    def from_json(cls, data):
        return cls(**dict([(str(k),v) for k,v in data.iteritems() 
                           if k in cls._VALID_ATTRIBUTES]))


class MapPost(Post):
    def __init__(self, **kwargs):
        Post.__init__(self, **kwargs)
        self.content = eval(self.content)

    def get_address(self):
        return self.content['address']

    def get_coordinates(self):
        return tuple(self.content['point'])

    def is_map(self):
        return True

class FilePost(Post):
    def is_file(self):
        return True

class _EmbedPost(Post):
    def is_embed(self):
        return self.content is not None

    def get_external_link(self):
        if not self.is_embed():
            return None
        return re.search(r'="(http.*?)"', self.content).group(1)

class ImagePost(_EmbedPost):
    def is_image(self):
        return True


class VideoPost(_EmbedPost):
    def is_video(self):
        return False

class HTMLPost(Post):
    def is_html(self):
        return True


class EmailPost(Post):
    def __init__(self, **kwargs):
        Post.__init__(self, **kwargs)
        self.__msg = None
    
    @property
    def msg(self):
        if not self.__msg:
            for f in self.files:
                if f.meta_data and \
                        f.meta_data.get('attachment_type') == 'email_message':
                    self.__msg = f
                    break
        return self.__msg

    def get_sender(self):
        return self.msg.meta_data['sender_display_name']

    def get_subject(self):
        return self.msg.meta_data['subject']

    def get_summary(self):
        return self.msg.meta_data['summary']
    
    def get_msg_content(self):
        return self.msg.retrieve()

    def is_email(self):
        return True

class EventPost(Post):
    def __init__(self, **kwargs):
        Post.__init__(self, **kwargs)
        self.__event = None
    
    @property
    def event(self):
        if not self.__event:
            for f in self.files:
                if f.meta_data and \
                        f.meta_data.get('attachment_type') == 'event':
                    self.__event = f
                    break
        return self.__event

    def get_ics_content(self):
        return self.event.retrieve()

    def is_event(self):
        return True

            
##### Exceptions #####
class ResourceException(Exception):
    pass

class InvalidRequest(Exception):
    pass

class ServiceError(Exception):
    pass
