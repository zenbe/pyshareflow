# Python library for Zenbe Shareflow API (v2) #

## Overview ##

This is a simple python library to interface with Zenbe's Shareflow
service.

This library was tested with Python 2.6.

Currently pyshareflow requires an API auth token. Your auth token is
displayed in the Shareflow interface. Select "All Flows" and click on
"options".

Alternatively, you can supply your login credentials to retrieve the
auth token via the API as demonstrated below.

API requests are scoped to a user. This means that a user of this API
only sees the flows and content they have access to. It also means
that any posts or comments made via the API show up in the web
interface with the user as the author.

## Operations ##

### Getting an API token ###

    >>> import pyshareflow
    >>> auth_token = pyshareflow.Api.get_auth_token('username', 'password',
    ...     'yourdomain.zenbe.com')


### Creating an API instance ###

    >>> import pyshareflow
    >>>	api = pyshareflow.Api('yourdomain.zenbe.com', 'auth token')

### Working with Users ###

Gets up to 50 users associated with any flow you are a member of.
Returns an array of `User` objects.

    >>> api.get_users()

Gets the next 50 users associated with any flow you are a member of.

    >>> api.get_users(offset=50)

Gets up to 50 users associated with the flow given by the id.

    >>> api.get_users(flow_id='flow id')

Returns a `User` object associated with user 33.

    >>> api.get_user(33)

Removes user 33 from the flow given by the flow id.

    >>> api.remove_user(33, 'flow id')

### Users ###

These are the attributes of `User` objects:

* `id`: An `int` id of the user 
* `login`: The login name of the user. Typically the same as the email address.
* `first_name`: The first name
* `last_name`: The last name
* `email`: The user's email address
* `avatar_url`: The url to fetch the user's avatar
* `is_online`: A `boolean` indicating if the user is logged in right
  now
* `time_zone`: The time zone string for the user

### Working with Flows ###

Retrieves an array of Flow objects, ordered by created at time. There
his a default limit of 30 flows, and a max limit of 100 flows.

    >>> flows = api.get_flows()

Returns up to 100 flows, ordered by when the flow was last updated.

    >>> flows = api.get_flows(limit=100, order_by='updated')

Returns up to 100 flows, offset by 100.

    >>> flows = api.get_flows(offset=100, limit=100)

Returns a list of all flows matching a particular name.

    >>> flows = api.get_flows(name='My Shareflow')
    >>> flows[0].name
    'My Shareflow'

A convenience method that returns a single flow matching the given
name. If multiple flows match only the first will be returned.

    >>> flows = api.get_flow_by_name('My Shareflow')

Create a new flow named 'My New Flow'. Returns the `Flow` object that
was created.

    >>> new_flow = api.create_flow('My New Flow')

Renames the flow with the given flow id and returns the new flow
object.

    >>> updated_flow = api.update_flow_name('New Flow Name', 'flow_id')

Invites a user to the flow. This sends an invitation email to the
user.

    >>> api.create_invitations('flow id', 'bob@example.com')

Invites all the email addresses specified in the array to the flow.

    >>> api.create_invitations('flow id', ['bob@example.com', sue@example.com'])

An invitation using an RFC2822 compliant email address.

    >>> api.create_invitations('flow id', "Bob Smith <bob@example.com>")

Deletes an invited user from a flow. The array syntax may also be used
to uninvite multiple invitees.

    >>> api.delete_invitations('flow id', 'bob@example.com')

Deletes a flow. _Be careful!_ All data will be deleted.

    >>> api.delete_flow('flow id')


### Flows ###

* `id`: The UUID of the flow
* `name`: The flow name
* `email_address`: The email address of the flow. Emails sent here show
  up on the flow
* `created_at`: A `datetime` object representing the flow creation time
* `updated_at`: A `datetime` object representing the flow update time
* `is_default`: A `boolean` indicating if the flow is your team's
  default flow
* `owner_name`: The creator of the flow
* `quota_percentage`: A `float` indicating the percentage of total
  storage space used by this flow.
* `quota_count`: An `int` representing the bytes used by this flow
* `rss_url`: The URL containing the RSS feed for this flow.
  invitation to this flow. See the description of `User` below.
* `invitations`: A list of `Invitation` objects representing users who
  have not yet accepted an invitation to the flow
* `owner_id`: The id of the user who created this flow.
  

### Invitations ###

* `id`: The uuid of the invitation
* `email`: The email address for the invitation

### Working with Posts ###

Retrieves the latest 30 posts across all flows, sorted by created at
time.

    >>> api.get_posts()

Returns the next 30 posts.

    >>> api.get_posts(offset=30)

Gets at most 100 posts for the given flow id, ordered by updated time.

    >>> api.get_posts(limit=100, flow_id='flow id', order_by='updated)

Gets the most recently updated 30 posts across flows, but excludes
comments.

    >>> api.get_posts(flow_id='flow id', include_comments=False, order_by='updated')

Gets the 30 posts created before the given `datetime` object.

    >>> api.get_posts(before=datetimeobj)

Gets any posts updated after the given `datetime` object. This query
is useful for checking for new activity.

    >>> api.get_posts(after=datetimeobj, order_by='updated')

Gets the posts in between the two dates. This is an exclusive
operation.

    >>> api.get_posts(before=begin, after=end)

Gets any posts matching the term 'presentation'. Will also search
comments, unless `include_comments=False`.

    >>> api.get_posts(search_term='presentation')

Executes the preceding search, but restricts it to a particular flow.

_Note_: For convenience there is also an `api.search(search_term)`
method.

    >>> api.get_posts(flow_id='flow id', search_term='presentation')

Uploads a file to the flow given by the flow id. Creates a new post.

    >>> api.post_files(r'C:\docs\planning.doc', 'flow_id')

Adds multiple files to the flow given by the flow id.

    >>> api.post_files([r'C:\docs\planning.doc', 
    ...	    r'C:\docs\schedule.xls'], 'flow_id')

Adds multiple files to the flow given by the id along with a comment
that will appear with the files.

    >>> api.post_files([r'C:\docs\planning.doc',
    ...    r'C:\docs\schedule.xls'], 'flow_id',
    ...    comment='Here are the files for the upcoming meeting.')

Adds file(s) to an existing post given by 'post_id'.

    >>> api.add_files_to_post(r'C:\docs\planning.doc', 'post_id')

Creates a post on the flow given by the id.

    >>> api.create_post('flow_id', 'This is some post content.')

Updates the post with the given id with the new content. Returns the
updated `Post` object.

    >>> api.update_post('post_id', 'New post content.')

Creates a comment associated with the post with the given id.

    >>> api.create_comment('post_id', 'This is a comment.')

Deletes the comment with the given id.

    >>> api.delete_comment('comment_id')

Permanently deletes the post (and any associated files and comments)
with the given id.

    >>> api.delete_post('post id')

Gets comments associated with a post. Only necessary if you specified
`include_comments=False` when fetching the post.

    >>> api.get_comments('post id')

### Posts ###

There are a few different post sub-types. These are the attributes
common to all posts.

* `id`: The post uuid
* `flow_id`: The id of the flow the post is part of
* `flow_name`: The name of the flow the post is part of
* `post_type`: A string describing the type of post
* `content`: The post content. May be empty for some post types
* `star`: The star indicator
* `created_at`: A `datetime` object representing when the post was created
* `updated_at`: A `datetime` object representing when the post was updated
* `reply_ids`: A `set` of ids of comments that are replies to this post
* `file_ids`: A `set` of ids of files associated with this post
* `user_id`: The id of the user responsible for this post
* `files`: A `list` of `File` objects associated with this post
* `comments`: A `list` of `Comment` objects associated with this post
* `user_id`: The user id of the user who authored this post  

### Post Subtypes ###

There are a few subtypes of a `Post`:

#### MapPost ####

Returned when a map was posted.

* `get_address()`: Returns the address of the map as a string.
* `get_coordinates()`: Returns the latitude and longitude coordinates as
  a tuple.  

#### FilePost ####

This is the type of post for any post containing files.

#### ImagePost ####

Indicates images are attached to this post. The corresponding `File`
objects will include dimension information as well as a URL to the
image thumbnail.

An ImagePost may also represent a link to an image on an external
service (Flickr for example). In that case, there may be no associated
files. To deal with this case:

    >>> if image_post.is_embed():
    ...    print image_post.get_external_link()
    ...
    http://www.flicker.com/foo

#### VideoPost ####

Indicates videos are attached to this post. This may also represent a
video linked to on an external service (like YouTube or Hulu). In that
case, use the `get_external_link()` method in the `ImagePost` example
to get the link to the video content.

#### HTMLPost ####

Indicates the `content` field of the post is HTML.

#### EmailPost ####

Indicates the post is an email. This type of post has a `msg`
attribute, which points to a `File` object representing the message.

The following methods are also available:

* `get_sender()`: Returns the display name of the sender.
* `get_subject()`: Returns the subject of the message.
* `get_summary()`: Returns a 255 character preview of the message.
* `get_msg_content()`: Downloads the full content of the message.
  

#### EventPost ####

Indicates the post is an event. This type of post has a `event`
attribute, which points to a `File` object representing the ICS
representation of the event.

The following methods are also available:

* `get_ics_content()`: Returns the ICS representation of the event
  
### Detecing Post Types ###

You can use `isinstance()` to detect post types. For convenience, all
posts implement the following methods, which return a `boolean`:

* `is_map()`
* `is_email()`
* `is_event()`
* `is_file()`
* `is_image()`
* `is_video()`
* `is_html()`
* `is_event()`
  

### Files ###

The following are attributes of `File` objects:

* `id`: The uuid of the file
* `file_name`: The name of the file
* `file_size`: The size (in bytes) of the file
* `post_id`: The uuid of the post this file is associated with
* `content_type`: The content type of the file
* `is_image`: Whether or not the file is an image
* `meta_data`: Metadata about the file. Only emails and event files have
  metadata.
* `width`: The width of the file (if it's an image)
* `height`: The height of the file (if it's an image)
* `thumbnail_url`: A thumbnail of the file. Usually only valid for
  images, but some documents may have thumbnails of their cover sheets
  as well.
* `created_at`: A `datetime` object representing when this file was created.
* `updated_at`: A `datetime` object representing when this file was updated.
* `url`: The URL this file can be retrieved from

Methods:

* `retrieve()`: Returns the retrieved file content.
  

### Comments ###

Comments are associated with `Post` objects. They have the following
attributes:

* `id`: The uuid of the comment
* `flow_id`: The id of the flow this comment is associated with
* `flow_name`: The name of the flow the comment is associated with
* `reply_to`: The post id this comment is a reply to
* `content`: The content of the comment
* `created_at`: A `datetime` object representing the creation time
* `updated_at`: A `datetime` object representing the update time
* `user_id`: The id of the user associated with this comment

## Exceptions ##

Any API method may throw an `HTTPException` when there are
HTTP-related errors.

There are 3 special exceptions:

### ResourceException ###

This is thrown if you are over-quota or are attempting to invite too
many users.

### InvalidRequest ###

This is thrown if you specify an invalid query, or try to modify an
read-only attribute.

### ServiceError ###

This happens when there is an internal server error (HTTP code 500) on
our part.

## TODO ##

* Implement a streaming file retrieve() operation
* Implement permalink attribute for Flows, Posts, Comments
* Add event posting
* Add map posting
* Docstrings
* Unit tests

